#!/usr/bin/env python3
"""Run frozen H002 source-reranking metrics.

This runner applies a C_e scorer fit on the internal H002 train split to the
source-wide official-validation candidate universe. Official validation rows are
eval-only: they are not used to fit the C_e scorer, tune lambda, or change the
frozen K/aggregation protocol.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from run_grouped_eval import read_json, read_jsonl, rel_path, stable_hash
from run_official_metric import (
    common_g_features,
    compatibility_features,
    fit_model,
    merge_features,
    safe_float,
    t_features,
    wrong_within_route_features,
)


SCHEMA_VERSION = "h002_source_reranking_metric_runner_v1"
STATUS_READY = "h002_source_reranking_metric_runner_ready"
STATUS_ERROR = "h002_source_reranking_metric_runner_errors"

EXPECTED_PROTOCOL_STATUS = "h002_source_reranking_metric_protocol_freeze_after_schema_audit_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze"
EXPECTED_MATERIALIZATION_STATUS = "h002_source_reranking_materialization_ready"
EXPECTED_TOTAL_ROWS = 762888
EXPECTED_PRIMARY_ROWS = 254296

TRAIN_SPLIT = "internal_train"
K_GRID = [5, 10, 20, 50, 100]
PRIMARY_FAMILIES = {"relative_vertical", "size_relative"}
SCORE_IDS = [
    "S0_source_score",
    "S1_Ce_only",
    "S2_source_x_Ce",
    "S3_log_source_plus_Ce",
    "C1_source_x_shuffled_Ce",
    "C2_source_x_wrong_T_Ce",
]
SELECTED_PREDICTION_SCORE_IDS = {"S0_source_score", "S2_source_x_Ce"}
SELECTED_PREDICTION_K = 100
CONTROL_SEED = "h002_source_reranking_metric_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--internal-split-dir", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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


def ce_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), common_g_features(row), compatibility_features(row))


def fit_ce_model(train_rows: list[dict[str, Any]], epochs: int, lr: float, l2: float) -> tuple[Any, float, dict[str, Any]]:
    return fit_model(train_rows, ce_feature_fn, epochs, lr, l2)


def predict_one(model: Any, prior: float, row: dict[str, Any], feature_fn: Any) -> float:
    if model is None:
        return prior
    return float(model.predict_one(feature_fn(row)))


def minmax_norm(value: float, bounds: tuple[float, float] | None) -> float:
    if bounds is None:
        return 0.5
    lo, hi = bounds
    if hi - lo <= 1e-12:
        return 0.5
    return (value - lo) / (hi - lo)


def clipped(value: float, eps: float = 1e-6) -> float:
    return min(max(value, eps), 1.0)


def update_bounds(bounds: dict[Any, list[float]], key: Any, value: float) -> None:
    if key not in bounds:
        bounds[key] = [value, value]
    else:
        bounds[key][0] = min(bounds[key][0], value)
        bounds[key][1] = max(bounds[key][1], value)


def frozen_score_values(
    record: dict[str, Any],
    source_bounds: dict[str, tuple[float, float]],
    ce_bounds: dict[tuple[str, str], tuple[float, float]],
) -> dict[str, float]:
    source_key = str(record["source_id"])
    ce_key = (str(record["source_id"]), str(record["route_family"]))
    norm_source = minmax_norm(record["source_score"], source_bounds.get(source_key))
    norm_ce = minmax_norm(record["ce_score"], ce_bounds.get(ce_key))
    norm_wrong = minmax_norm(record["wrong_ce_score"], ce_bounds.get(ce_key))
    norm_shuffled = minmax_norm(record["shuffled_ce_score"], ce_bounds.get(ce_key))
    s = clipped(norm_source)
    c = clipped(norm_ce)
    w = clipped(norm_wrong)
    h = clipped(norm_shuffled)
    return {
        "S0_source_score": norm_source,
        "S1_Ce_only": norm_ce,
        "S2_source_x_Ce": s * c,
        "S3_log_source_plus_Ce": math.log(s) + math.log(c),
        "C1_source_x_shuffled_Ce": s * h,
        "C2_source_x_wrong_T_Ce": s * w,
    }


def gt_key(record: dict[str, Any]) -> str:
    return "|".join(
        [
            str(record["scan_id"]),
            str(record["subject_id"]),
            str(record["object_id"]),
            str(record["predicate_label"]),
        ]
    )


def selected_sort_key(score_id: str, record: dict[str, Any]) -> tuple[float, float, str]:
    return (
        float(record["scores"].get(score_id, 0.0)),
        float(record.get("source_score", 0.0)),
        str(record.get("prediction_id", "")),
    )


def group_records(records: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["source_id"], record["subgraph_id"], record["route_family"])].append(record)
    return grouped


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


def finalize_metric_row(base: dict[str, Any], acc: dict[str, Any]) -> dict[str, Any]:
    recall = None
    if acc["gt_total"] > 0:
        recall = acc["gt_selected"] / acc["gt_total"]
    violation_rate = None
    if acc["violation_denominator"] > 0:
        violation_rate = acc["violation_count"] / acc["violation_denominator"]
    selected_mean = None
    if acc["unit_count"] > 0:
        selected_mean = acc["selected_total"] / acc["unit_count"]
    return {
        **base,
        "unit_count": acc["unit_count"],
        "gt_units": acc["gt_units"],
        "gt_total": acc["gt_total"],
        "gt_selected": acc["gt_selected"],
        "Recall@K": recall,
        "selected_total": acc["selected_total"],
        "Selected@K_mean": selected_mean,
        "violation_denominator": acc["violation_denominator"],
        "violation_count": acc["violation_count"],
        "Violation@K": violation_rate,
    }


def metric_tables(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = group_records(records)
    family_acc: dict[tuple[str, str, str, int], dict[str, Any]] = defaultdict(empty_accumulator)
    selected_rows: list[dict[str, Any]] = []

    for group_key, bucket in grouped.items():
        denom_gt = {gt_key(record) for record in bucket if record["gt_exact_match"]}
        for score_id in SCORE_IDS:
            ranked = sorted(bucket, key=lambda record: selected_sort_key(score_id, record), reverse=True)
            for k in K_GRID:
                selected = ranked[: min(k, len(ranked))]
                selected_gt = {gt_key(record) for record in selected if record["gt_exact_match"]}
                acc_key = (group_key[0], group_key[2], score_id, k)
                add_group_metric(family_acc[acc_key], denom_gt, selected_gt, selected)
                if score_id in SELECTED_PREDICTION_SCORE_IDS and k == SELECTED_PREDICTION_K:
                    for rank, record in enumerate(selected, start=1):
                        selected_rows.append(
                            {
                                "score_id": score_id,
                                "K": k,
                                "rank": rank,
                                "candidate_id": record["candidate_id"],
                                "source_id": record["source_id"],
                                "subgraph_id": record["subgraph_id"],
                                "route_family": record["route_family"],
                                "predicate_label": record["predicate_label"],
                                "gt_exact_match": record["gt_exact_match"],
                                "violation_status": record["violation_status"],
                                "violation_checkable": record["violation_checkable"],
                                "score": record["scores"][score_id],
                            }
                        )

    source_family_rows: list[dict[str, Any]] = []
    for (source_id, family, score_id, k), acc in sorted(family_acc.items()):
        source_family_rows.append(
            finalize_metric_row(
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
        )

    aggregate_rows: list[dict[str, Any]] = []
    rows_by_score_k: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in source_family_rows:
        rows_by_score_k[(row["score_id"], int(row["K"]))].append(row)
    for (score_id, k), rows in sorted(rows_by_score_k.items()):
        for scope, scoped in [
            ("primary_success_weighted", [row for row in rows if row["route_family"] in PRIMARY_FAMILIES]),
            ("all_weighted", rows),
        ]:
            acc = empty_accumulator()
            for row in scoped:
                acc["unit_count"] += int(row["unit_count"])
                acc["gt_units"] += int(row["gt_units"])
                acc["gt_total"] += int(row["gt_total"])
                acc["gt_selected"] += int(row["gt_selected"])
                acc["selected_total"] += int(row["selected_total"])
                acc["violation_denominator"] += int(row["violation_denominator"])
                acc["violation_count"] += int(row["violation_count"])
            aggregate_rows.append(
                finalize_metric_row(
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
        primary_rows = [row for row in rows if row["route_family"] in PRIMARY_FAMILIES]
        recall_values = [safe_float(row["Recall@K"], None) for row in primary_rows if row["Recall@K"] != "" and row["Recall@K"] is not None]
        violation_values = [safe_float(row["Violation@K"], None) for row in primary_rows if row["Violation@K"] != "" and row["Violation@K"] is not None]
        aggregate_rows.append(
            {
                "level": "primary_success_macro",
                "source_id": "ALL",
                "route_family": "PRIMARY",
                "score_id": score_id,
                "K": k,
                "source_family_rows": len(primary_rows),
                "Recall@K": sum(recall_values) / len(recall_values) if recall_values else None,
                "Violation@K": sum(violation_values) / len(violation_values) if violation_values else None,
            }
        )

    controls: list[dict[str, Any]] = []
    by_key = {(row["level"], row["score_id"], int(row["K"])): row for row in aggregate_rows}
    for k in K_GRID:
        primary = by_key.get(("primary_success_weighted", "S2_source_x_Ce", k))
        if not primary:
            continue
        for baseline_id, expectation in [
            ("S0_source_score", "source_baseline"),
            ("S1_Ce_only", "C_e_only_diagnostic"),
            ("C1_source_x_shuffled_Ce", "shuffled_Ce_control_should_degrade"),
            ("C2_source_x_wrong_T_Ce", "wrong_T_control_should_degrade"),
        ]:
            baseline = by_key.get(("primary_success_weighted", baseline_id, k))
            if not baseline:
                continue
            p_recall = primary.get("Recall@K")
            b_recall = baseline.get("Recall@K")
            p_violation = primary.get("Violation@K")
            b_violation = baseline.get("Violation@K")
            controls.append(
                {
                    "level": "primary_success_weighted",
                    "K": k,
                    "comparison": f"S2_vs_{baseline_id}",
                    "expectation": expectation,
                    "primary_score": "S2_source_x_Ce",
                    "baseline_score": baseline_id,
                    "primary_Recall@K": p_recall,
                    "baseline_Recall@K": b_recall,
                    "delta_Recall@K": None if p_recall is None or b_recall is None else p_recall - b_recall,
                    "primary_Violation@K": p_violation,
                    "baseline_Violation@K": b_violation,
                    "delta_Violation@K": None if p_violation is None or b_violation is None else p_violation - b_violation,
                }
            )
    return source_family_rows, aggregate_rows, controls, selected_rows


def validate_inputs(protocol_dir: Path, materialization_dir: Path, protocol: dict[str, Any], materialization: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol.get("status")})
    if protocol.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol.get("next_todo")})
    if protocol.get("validation_errors") not in (0, []):
        errors.append({"error_type": "protocol_validation_errors_present", "actual": protocol.get("validation_errors")})
    decision = protocol.get("decision", {})
    if decision.get("metric_protocol_frozen") is not True:
        errors.append({"error_type": "metric_protocol_not_frozen"})
    if decision.get("metrics_run_in_this_stage") is not False:
        errors.append({"error_type": "protocol_boundary_already_ran_metric"})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "protocol_used_official_test"})
    if decision.get("C_e_excludes_Z_e") is not True:
        errors.append({"error_type": "protocol_allows_Ze_inside_Ce"})

    if materialization.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_materialization_status", "actual": materialization.get("status")})
    if materialization.get("official_test_usage") is not False:
        errors.append({"error_type": "materialization_used_official_test"})
    if materialization.get("source_reranking_metrics_run") is not False:
        errors.append({"error_type": "materialization_already_ran_source_metric"})
    if materialization.get("row_counts", {}).get("total_rows") != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "unexpected_total_rows", "actual": materialization.get("row_counts", {}).get("total_rows")})
    if materialization.get("row_counts", {}).get("primary_success_family_rows") != EXPECTED_PRIMARY_ROWS:
        errors.append(
            {
                "error_type": "unexpected_primary_rows",
                "actual": materialization.get("row_counts", {}).get("primary_success_family_rows"),
            }
        )
    for filename in ["model_safe_ce_view.jsonl", "source_rank_view.jsonl", "hidden_metric_manifest.jsonl"]:
        if not (materialization_dir / filename).exists():
            errors.append({"error_type": "missing_required_input", "file": filename})
    for filename in ["score_contract.csv", "metric_protocol.csv", "recall_protocol.csv", "violation_protocol.csv"]:
        if not (protocol_dir / filename).exists():
            errors.append({"error_type": "missing_protocol_file", "file": filename})
    return errors


def score_source_rows(args: argparse.Namespace, model: Any, prior: float) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    materialization_dir = args.materialization_dir
    ce_path = materialization_dir / "model_safe_ce_view.jsonl"
    rank_path = materialization_dir / "source_rank_view.jsonl"
    hidden_path = materialization_dir / "hidden_metric_manifest.jsonl"

    records: list[dict[str, Any]] = []
    source_bounds_raw: dict[str, list[float]] = {}
    ce_bounds_raw: dict[tuple[str, str], list[float]] = {}
    row_errors: list[dict[str, Any]] = []
    source_counts = Counter()
    family_counts = Counter()

    with ce_path.open("r", encoding="utf-8") as ce_handle, rank_path.open("r", encoding="utf-8") as rank_handle, hidden_path.open("r", encoding="utf-8") as hidden_handle:
        for line_index, (ce_line, rank_line, hidden_line) in enumerate(zip(ce_handle, rank_handle, hidden_handle), start=1):
            ce_row = json.loads(ce_line)
            rank_row = json.loads(rank_line)
            hidden_row = json.loads(hidden_line)
            candidate_id = str(ce_row.get("candidate_id"))
            if candidate_id != rank_row.get("candidate_id") or candidate_id != hidden_row.get("candidate_id"):
                row_errors.append(
                    {
                        "line": line_index,
                        "error_type": "candidate_id_alignment_mismatch",
                        "ce": candidate_id,
                        "rank": rank_row.get("candidate_id"),
                        "hidden": hidden_row.get("candidate_id"),
                    }
                )
                if len(row_errors) >= 20:
                    break
                continue

            source_id = str(ce_row.get("source_id"))
            family = str(ce_row.get("route_family"))
            source_score = safe_float(rank_row.get("Z_e", {}).get("ranking_score"), 0.0)
            ce_score = predict_one(model, prior, ce_row, ce_feature_fn)
            wrong_ce_score = predict_one(model, prior, ce_row, wrong_within_route_features)
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
                "wrong_ce_score": wrong_ce_score,
                "shuffled_ce_score": ce_score,
                "gt_exact_match": bool(hidden_row.get("gt_exact_match")),
                "violation_status": str(hidden_row.get("h2_relation_status")),
                "violation_checkable": violation_checkable,
                "scores": {},
            }
            records.append(record)
            source_counts[source_id] += 1
            family_counts[family] += 1
            update_bounds(source_bounds_raw, source_id, source_score)
            update_bounds(ce_bounds_raw, (source_id, family), ce_score)

    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        buckets[(record["source_id"], record["route_family"])].append(record)
    for bucket_key, bucket in buckets.items():
        ordered = sorted(bucket, key=lambda record: stable_hash(f"{CONTROL_SEED}:shuffle:{record['candidate_id']}"))
        if len(ordered) <= 1:
            continue
        shifted = ordered[1:] + ordered[:1]
        for record, donor in zip(ordered, shifted):
            record["shuffled_ce_score"] = donor["ce_score"]

    source_bounds = {key: (values[0], values[1]) for key, values in source_bounds_raw.items()}
    ce_bounds = {key: (values[0], values[1]) for key, values in ce_bounds_raw.items()}
    for record in records:
        record["scores"] = frozen_score_values(record, source_bounds, ce_bounds)

    score_summary = {
        "row_count": len(records),
        "source_counts": dict(sorted(source_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "source_score_bounds": {key: {"min": lo, "max": hi} for key, (lo, hi) in sorted(source_bounds.items())},
        "ce_score_bounds": {f"{source}|{family}": {"min": lo, "max": hi} for (source, family), (lo, hi) in sorted(ce_bounds.items())},
    }
    return records, score_summary, row_errors


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol_dir / "summary.json")
    materialization = read_json(args.materialization_dir / "row_manifest.json")
    errors = validate_inputs(args.protocol_dir, args.materialization_dir, protocol, materialization)

    train_rows = [row for row in read_jsonl(args.internal_split_dir / "model_safe_split_view.jsonl") if row.get("protocol_split") == TRAIN_SPLIT]
    if not train_rows:
        errors.append({"error_type": "empty_internal_train_rows"})

    model = None
    prior = 0.5
    fit_summary: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    score_summary: dict[str, Any] = {}
    source_family_metrics: list[dict[str, Any]] = []
    score_condition_metrics: list[dict[str, Any]] = []
    control_metrics: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []

    if not errors:
        model, prior, fit_summary = fit_ce_model(train_rows, args.epochs, args.lr, args.l2)
        records, score_summary, row_errors = score_source_rows(args, model, prior)
        errors.extend(row_errors)
        if len(records) != EXPECTED_TOTAL_ROWS:
            errors.append({"error_type": "scored_row_count_mismatch", "actual": len(records), "expected": EXPECTED_TOTAL_ROWS})
        if not errors:
            source_family_metrics, score_condition_metrics, control_metrics, selected_rows = metric_tables(records)

    status = STATUS_READY if not errors else STATUS_ERROR
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_artifacts": {
            "protocol_dir": rel_path(args.repo_root, args.protocol_dir),
            "materialization_dir": rel_path(args.repo_root, args.materialization_dir),
            "internal_split_view": rel_path(args.repo_root, args.internal_split_dir / "model_safe_split_view.jsonl"),
        },
        "row_counts": {
            "internal_train": len(train_rows),
            "source_rows_scored": len(records),
            "selected_prediction_rows": len(selected_rows),
        },
        "model": {
            "C_e_train_split": TRAIN_SPLIT,
            "fit_or_tune_on_official_validation": False,
            "official_test_usage": False,
            "feature_blocks": ["T_e", "G_e"],
            "fit_summary": fit_summary,
        },
        "score_summary": score_summary,
        "outputs": {
            "metric_manifest": rel_path(args.repo_root, args.out / "metric_manifest.json"),
            "score_manifest": rel_path(args.repo_root, args.out / "score_manifest.json"),
            "source_family_metrics": rel_path(args.repo_root, args.out / "source_family_metrics.csv"),
            "score_condition_metrics": rel_path(args.repo_root, args.out / "score_condition_metrics.csv"),
            "control_metrics": rel_path(args.repo_root, args.out / "control_metrics.csv"),
            "selected_predictions": rel_path(args.repo_root, args.out / "selected_predictions.jsonl"),
            "validation_errors": rel_path(args.repo_root, args.out / "validation_errors.jsonl"),
        },
        "boundary": {
            "source_reranking_metric_produced": status == STATUS_READY,
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "C_e_excludes_Z_e": True,
            "Z_e_combined_only_after_C_e": True,
            "post_hoc_lambda_tuning": False,
            "support_contact_success_aggregation": "excluded_diagnostic",
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
        },
        "next_todo": "compatibility_dataset_v3_source_reranking_metric_result_review_after_runner",
        "validation_errors": len(errors),
    }

    score_manifest = {
        "schema_version": f"{SCHEMA_VERSION}_score_manifest",
        "score_ids": SCORE_IDS,
        "primary_score": "S2_source_x_Ce",
        "normalization": {
            "source_score": "per_source_minmax",
            "C_e_score": "per_source_family_minmax",
            "lambda": "fixed_1_for_S3_only",
        },
        "score_summary": score_summary,
        "model_fit_summary": fit_summary,
    }

    write_json(args.out / "metric_manifest.json", manifest)
    write_json(args.out / "score_manifest.json", score_manifest)
    write_csv(args.out / "source_family_metrics.csv", source_family_metrics)
    write_csv(args.out / "score_condition_metrics.csv", score_condition_metrics)
    write_csv(args.out / "control_metrics.csv", control_metrics)
    write_jsonl(args.out / "selected_predictions.jsonl", selected_rows)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    return manifest


def main() -> int:
    args = parse_args()
    manifest = run(args)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
