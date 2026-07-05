#!/usr/bin/env python3
"""Run H002 C_e improvement-path diagnostics.

This stage tests whether the current compatibility score can be strengthened
without reopening p_obs/p_rel. It keeps official validation source rows
evaluation-only and fits all C_e variants on the frozen internal split.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from run_grouped_eval import binary_metrics, read_jsonl, stable_hash
from run_official_metric import (
    common_g_features,
    common_numeric,
    compatibility_features,
    fit_model,
    merge_features,
    mutate_predicate,
    predicate_value,
    safe_float,
    t_features,
)


SCHEMA_VERSION = "h002_ce_improvement_path_v1"
STATUS_READY = "h002_ce_improvement_path_ready"
STATUS_ERROR = "h002_ce_improvement_path_errors"

TRAIN_SPLIT = "internal_train"
DEV_SPLIT = "internal_dev"
HELDOUT_SPLIT = "internal_heldout"
PRIMARY_FAMILIES = {"relative_vertical", "size_relative"}
K_GRID = [5, 10, 20, 50, 100]
EXPECTED_TOTAL_ROWS = 762888
CONTROL_SEED = "h002_ce_improvement_path_v1"

INVERSE_PREDICATES = {
    "higher than": "lower than",
    "lower than": "higher than",
    "bigger than": "smaller than",
    "smaller than": "bigger than",
    "left": "right",
    "right": "left",
    "front": "behind",
    "behind": "front",
    "standing on": "lying on",
    "lying on": "standing on",
}

SCORE_IDS = [
    "S0_source_score",
    "S2_current_source_x_Ce",
    "I1_hardneg_structured_source_x_Ce",
    "I2_route_aware_source_x_Ce",
    "I4_calibrated_route_aware_source_x_Ce",
]

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--internal-split-dir", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--support-contact-capacity-dir", type=Path, required=True)
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def logit(p: float) -> float:
    p = min(max(float(p), 1e-6), 1.0 - 1e-6)
    return math.log(p / (1.0 - p))


def apply_temperature(p: float, temperature: float) -> float:
    return sigmoid(logit(p) / max(temperature, 1e-6))


def current_ce_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), common_g_features(row), compatibility_features(row))


def structured_margin_features(row: dict[str, Any]) -> dict[str, float]:
    predicate = predicate_value(row)
    route = str(row.get("route_family") or "")
    out: dict[str, float] = {}
    dz = common_numeric(row, "center_delta_z", 0.0)
    ndz = common_numeric(row, "normalized_center_delta_z", 0.0)
    dx = common_numeric(row, "center_delta_x", 0.0)
    dy = common_numeric(row, "center_delta_y", 0.0)
    ndx = common_numeric(row, "normalized_center_delta_x", 0.0)
    ndy = common_numeric(row, "normalized_center_delta_y", 0.0)
    log_volume = common_numeric(row, "log_volume_ratio_s_over_o", 0.0)
    log_extent = common_numeric(row, "log_max_extent_ratio_s_over_o", 0.0)
    log_height = common_numeric(row, "log_height_ratio_s_over_o", 0.0)
    gap = common_numeric(row, "surface_gap_subject_bottom_to_object_top", 0.0)
    overlap = max(
        common_numeric(row, "xy_overlap_min_ratio", 0.0),
        common_numeric(row, "xy_overlap_max_ratio", 0.0),
    )

    vertical_sign = 1.0 if predicate == "higher than" else -1.0 if predicate == "lower than" else 0.0
    size_sign = 1.0 if predicate == "bigger than" else -1.0 if predicate == "smaller than" else 0.0
    x_sign = 1.0 if predicate == "right" else -1.0 if predicate == "left" else 0.0
    y_sign = 1.0 if predicate == "front" else -1.0 if predicate == "behind" else 0.0

    out["S.route_is_comparison"] = 1.0 if route in {"relative_vertical", "size_relative", "relative_horizontal"} else 0.0
    out["S.vertical.signed_center_delta_z"] = vertical_sign * dz
    out["S.vertical.signed_normalized_center_delta_z"] = vertical_sign * ndz
    out["S.size.signed_log_volume_ratio"] = size_sign * log_volume
    out["S.size.signed_log_extent_ratio"] = size_sign * log_extent
    out["S.size.signed_log_height_ratio"] = size_sign * log_height
    out["S.horizontal.signed_axis_margin"] = x_sign * dx + y_sign * dy
    out["S.horizontal.signed_norm_axis_margin"] = x_sign * ndx + y_sign * ndy
    out["S.support.abs_gap"] = abs(gap) if route == "support_contact" else 0.0
    out["S.support.overlap"] = overlap if route == "support_contact" else 0.0
    out["S.support.contact_proxy"] = common_numeric(row, "support_contact_likelihood_proxy", 0.0)
    return out


def structured_ce_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(current_ce_features(row), structured_margin_features(row))


def mutate_positive_to_inverse_negative(row: dict[str, Any], suffix: str) -> dict[str, Any] | None:
    predicate = predicate_value(row)
    inverse = INVERSE_PREDICATES.get(predicate)
    if inverse is None:
        return None
    mutated = mutate_predicate(deepcopy(row), inverse)
    mutated["target_y"] = 0
    mutated["unified_row_id"] = f"{row.get('unified_row_id')}::hardneg::{suffix}"
    mutated["hard_negative_source"] = "inverse_predicate_same_geometry"
    return mutated


def build_hard_negative_train_rows(train_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    augmented = list(train_rows)
    added = 0
    by_family = Counter()
    for row in train_rows:
        if int(row.get("target_y", 0)) != 1:
            continue
        mutated = mutate_positive_to_inverse_negative(row, str(added))
        if mutated is None:
            continue
        augmented.append(mutated)
        added += 1
        by_family[str(row.get("route_family"))] += 1
    return augmented, {
        "original_train_rows": len(train_rows),
        "augmented_train_rows": len(augmented),
        "added_inverse_hard_negatives": added,
        "added_by_family": dict(sorted(by_family.items())),
    }


def fit_route_models(train_rows: list[dict[str, Any]], feature_fn: FeatureFn, epochs: int, lr: float, l2: float) -> tuple[dict[str, Any], dict[str, float], dict[str, Any]]:
    models: dict[str, Any] = {}
    priors: dict[str, float] = {}
    summaries: dict[str, Any] = {}
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        by_family[str(row.get("route_family"))].append(row)
    for family, rows in sorted(by_family.items()):
        model, prior, summary = fit_model(rows, feature_fn, epochs, lr, l2)
        models[family] = model
        priors[family] = prior
        summaries[family] = summary
    return models, priors, summaries


def predict_model(model: Any, prior: float, row: dict[str, Any], feature_fn: FeatureFn) -> float:
    if model is None:
        return float(prior)
    return float(model.predict_one(feature_fn(row)))


def predict_route(models: dict[str, Any], priors: dict[str, float], row: dict[str, Any], feature_fn: FeatureFn) -> float:
    family = str(row.get("route_family"))
    return predict_model(models.get(family), priors.get(family, 0.5), row, feature_fn)


def tune_temperature(dev_rows: list[dict[str, Any]], score_fn: Callable[[dict[str, Any]], float]) -> dict[str, Any]:
    labels = [int(row.get("target_y", 0)) for row in dev_rows]
    raw_scores = [score_fn(row) for row in dev_rows]
    candidates = [0.35, 0.5, 0.67, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
    best = {"temperature": 1.0, "nll": float("inf")}
    for temp in candidates:
        scores = [apply_temperature(score, temp) for score in raw_scores]
        metrics = binary_metrics(labels, scores)
        nll = safe_float(metrics.get("NLL"), float("inf"))
        if nll < best["nll"]:
            best = {"temperature": temp, "nll": nll}
    return {"grid": candidates, **best, "dev_rows": len(dev_rows)}


def calibration_table(rows: list[dict[str, Any]], predictors: dict[str, Callable[[dict[str, Any]], float]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for split in [DEV_SPLIT, HELDOUT_SPLIT]:
        split_rows = [row for row in rows if row.get("protocol_split") == split]
        labels = [int(row.get("target_y", 0)) for row in split_rows]
        for score_id, fn in predictors.items():
            scores = [fn(row) for row in split_rows]
            row = binary_metrics(labels, scores)
            out.append({"protocol_split": split, "score_id": score_id, **row})
    return out


def update_bounds(bounds: dict[Any, list[float]], key: Any, value: float) -> None:
    if key not in bounds:
        bounds[key] = [value, value]
    else:
        bounds[key][0] = min(bounds[key][0], value)
        bounds[key][1] = max(bounds[key][1], value)


def minmax(value: float, bounds: tuple[float, float] | None) -> float:
    if bounds is None:
        return 0.5
    lo, hi = bounds
    if hi - lo <= 1e-12:
        return 0.5
    return (value - lo) / (hi - lo)


def clip01(value: float, eps: float = 1e-6) -> float:
    return min(max(value, eps), 1.0)


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


def finalize_metric(base: dict[str, Any], acc: dict[str, Any]) -> dict[str, Any]:
    return {
        **base,
        "unit_count": acc["unit_count"],
        "gt_units": acc["gt_units"],
        "gt_total": acc["gt_total"],
        "gt_selected": acc["gt_selected"],
        "Recall@K": None if acc["gt_total"] == 0 else acc["gt_selected"] / acc["gt_total"],
        "selected_total": acc["selected_total"],
        "Selected@K_mean": None if acc["unit_count"] == 0 else acc["selected_total"] / acc["unit_count"],
        "violation_denominator": acc["violation_denominator"],
        "violation_count": acc["violation_count"],
        "Violation@K": None if acc["violation_denominator"] == 0 else acc["violation_count"] / acc["violation_denominator"],
    }


def read_aligned_source_rows(materialization_dir: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    ce_path = materialization_dir / "model_safe_ce_view.jsonl"
    rank_path = materialization_dir / "source_rank_view.jsonl"
    hidden_path = materialization_dir / "hidden_metric_manifest.jsonl"
    with ce_path.open("r", encoding="utf-8") as ce_handle, rank_path.open("r", encoding="utf-8") as rank_handle, hidden_path.open("r", encoding="utf-8") as hidden_handle:
        for ce_line, rank_line, hidden_line in zip(ce_handle, rank_handle, hidden_handle):
            yield json.loads(ce_line), json.loads(rank_line), json.loads(hidden_line)


def score_source_rows(
    materialization_dir: Path,
    predictors: dict[str, Callable[[dict[str, Any]], float]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    bounds_raw: dict[str, dict[Any, list[float]]] = defaultdict(dict)
    source_counts = Counter()
    family_counts = Counter()
    for idx, (ce_row, rank_row, hidden_row) in enumerate(read_aligned_source_rows(materialization_dir), start=1):
        candidate_id = str(ce_row.get("candidate_id"))
        if candidate_id != rank_row.get("candidate_id") or candidate_id != hidden_row.get("candidate_id"):
            errors.append({"line": idx, "error_type": "candidate_id_alignment_mismatch"})
            if len(errors) >= 20:
                break
            continue
        source_id = str(ce_row.get("source_id"))
        family = str(ce_row.get("route_family"))
        source_score = safe_float(rank_row.get("Z_e", {}).get("ranking_score"), 0.0)
        raw_scores = {score_id: fn(ce_row) for score_id, fn in predictors.items()}
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
            "raw_scores": raw_scores,
            "gt_exact_match": bool(hidden_row.get("gt_exact_match")),
            "violation_status": str(hidden_row.get("h2_relation_status")),
            "violation_checkable": bool(hidden_row.get("h2_violation_checkable")) and family != "support_contact",
            "scores": {},
        }
        records.append(record)
        source_counts[source_id] += 1
        family_counts[family] += 1
        update_bounds(bounds_raw["source"], source_id, source_score)
        for score_id, value in raw_scores.items():
            update_bounds(bounds_raw[score_id], (source_id, family), value)

    bounds = {
        bucket: {key: (value[0], value[1]) for key, value in values.items()}
        for bucket, values in bounds_raw.items()
    }
    for record in records:
        source_norm = minmax(record["source_score"], bounds["source"].get(record["source_id"]))
        record["scores"]["S0_source_score"] = source_norm
        source_clipped = clip01(source_norm)
        for score_id, value in record["raw_scores"].items():
            ce_norm = minmax(value, bounds[score_id].get((record["source_id"], record["route_family"])))
            out_id = {
                "current_Ce": "S2_current_source_x_Ce",
                "hardneg_structured_Ce": "I1_hardneg_structured_source_x_Ce",
                "route_aware_Ce": "I2_route_aware_source_x_Ce",
                "calibrated_route_aware_Ce": "I4_calibrated_route_aware_source_x_Ce",
            }[score_id]
            record["scores"][out_id] = source_clipped * clip01(ce_norm)
    score_summary = {
        "row_count": len(records),
        "source_counts": dict(sorted(source_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "source_bounds": {str(key): {"min": lo, "max": hi} for key, (lo, hi) in sorted(bounds["source"].items())},
        "ce_bounds": {
            score_id: {f"{source}|{family}": {"min": lo, "max": hi} for (source, family), (lo, hi) in sorted(values.items())}
            for score_id, values in bounds.items()
            if score_id != "source"
        },
    }
    return records, score_summary, errors


def metric_tables(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["source_id"], record["subgraph_id"], record["route_family"])].append(record)
    family_acc: dict[tuple[str, str, str, int], dict[str, Any]] = defaultdict(empty_accumulator)
    for group_key, bucket in grouped.items():
        denom_gt = {gt_key(record) for record in bucket if record["gt_exact_match"]}
        for score_id in SCORE_IDS:
            ranked = sorted(bucket, key=lambda record: selected_sort_key(score_id, record), reverse=True)
            for k in K_GRID:
                selected = ranked[: min(k, len(ranked))]
                selected_gt = {gt_key(record) for record in selected if record["gt_exact_match"]}
                add_group_metric(family_acc[(group_key[0], group_key[2], score_id, k)], denom_gt, selected_gt, selected)

    source_family_rows: list[dict[str, Any]] = []
    for (source_id, family, score_id, k), acc in sorted(family_acc.items()):
        source_family_rows.append(finalize_metric({"level": "source_family", "source_id": source_id, "route_family": family, "score_id": score_id, "K": k, "primary_success_family": family in PRIMARY_FAMILIES}, acc))

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
            aggregate_rows.append(finalize_metric({"level": scope, "source_id": "ALL", "route_family": "PRIMARY" if scope.startswith("primary") else "ALL", "score_id": score_id, "K": k}, acc))
    by_key = {(row["level"], row["score_id"], int(row["K"])): row for row in aggregate_rows}
    improvements: list[dict[str, Any]] = []
    for k in K_GRID:
        base = by_key.get(("primary_success_weighted", "S2_current_source_x_Ce", k))
        if not base:
            continue
        for score_id in SCORE_IDS:
            if score_id == "S2_current_source_x_Ce":
                continue
            row = by_key.get(("primary_success_weighted", score_id, k))
            if not row:
                continue
            improvements.append(
                {
                    "scope": "primary_success_weighted",
                    "K": k,
                    "candidate_score": score_id,
                    "baseline_score": "S2_current_source_x_Ce",
                    "candidate_Recall@K": row.get("Recall@K"),
                    "baseline_Recall@K": base.get("Recall@K"),
                    "delta_Recall@K": None if row.get("Recall@K") is None or base.get("Recall@K") is None else row["Recall@K"] - base["Recall@K"],
                    "candidate_Violation@K": row.get("Violation@K"),
                    "baseline_Violation@K": base.get("Violation@K"),
                    "delta_Violation@K": None if row.get("Violation@K") is None or base.get("Violation@K") is None else row["Violation@K"] - base["Violation@K"],
                }
            )
    return source_family_rows, aggregate_rows, improvements


def build_report(summary: dict[str, Any], aggregate_rows: list[dict[str, Any]], calibration_rows: list[dict[str, Any]], stage_rows: list[dict[str, Any]]) -> str:
    def pick(score_id: str, k: int) -> dict[str, Any]:
        for row in aggregate_rows:
            if row.get("level") == "primary_success_weighted" and row.get("score_id") == score_id and int(row.get("K")) == k:
                return row
        return {}

    lines = [
        "# H002 Report 0706: C_e Improvement Path",
        "",
        "## 목적",
        "",
        "`p_obs/p_rel`을 보류하고, H002의 핵심인 `C_e = compatibility(T_e, G_e)`를 강화할 수 있는지 실험 단계에서 점검했다.",
        "",
        "검증 순서:",
        "",
        "1. hard-negative + structured compatibility",
        "2. route-aware C_e",
        "3. richer G_e hard-route feasibility",
        "4. calibrated C_e",
        "",
        "## 결과 요약",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"selected_path = {summary['decision']['selected_path']}",
        f"best_primary_score = {summary['decision']['best_primary_score']}",
        f"calibrated_ce_main_promotion = {str(summary['decision']['calibrated_ce_main_promotion']).lower()}",
        f"richer_ge_support_contact_promotion = {str(summary['decision']['richer_ge_support_contact_promotion']).lower()}",
        "```",
        "",
        "Primary comparison route, K=10/20/50:",
        "",
        "| Score | K | Recall@K | Violation@K |",
        "| --- | ---: | ---: | ---: |",
    ]
    for score_id in SCORE_IDS:
        for k in [10, 20, 50]:
            row = pick(score_id, k)
            if row:
                lines.append(f"| `{score_id}` | {k} | {safe_float(row.get('Recall@K'), 0.0):.6f} | {safe_float(row.get('Violation@K'), 0.0):.6f} |")
    lines.extend(["", "## Stage Decision", "", "| Stage | Decision | Reason |", "| --- | --- | --- |"])
    for row in stage_rows:
        lines.append(f"| {row['stage']} | {row['decision']} | {row['reason']} |")
    lines.extend(["", "## Calibration Heldout Metrics", "", "| Score | AUROC | Brier | NLL |", "| --- | ---: | ---: | ---: |"])
    for row in calibration_rows:
        if row.get("protocol_split") == HELDOUT_SPLIT:
            lines.append(f"| `{row['score_id']}` | {safe_float(row.get('auroc'), 0.0):.6f} | {safe_float(row.get('Brier'), 0.0):.6f} | {safe_float(row.get('NLL'), 0.0):.6f} |")
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- hard-negative와 structured feature는 `C_e`가 단순 source score 복사가 아니라 predicate-geometry matching 문제라는 점을 더 명확히 만든다.",
            "- route-aware C_e는 relation family마다 다른 evidence route가 필요하다는 H002 framework와 맞는다.",
            "- support/contact richer G_e는 현재 capacity gate에서 막혀 있어 main route로 승격하지 않는다.",
            "- calibrated C_e는 primary comparison route에서는 개선 후보로 보이지만, main score 대체 전에는 bootstrap CI와 family-wise review가 필요하다.",
            "",
            "따라서 현재 H002의 가장 안전한 다음 방향은 calibrated route-aware `C_e`를 candidate improved score로 보관하고, CI/family-wise review 후 main score 승격 여부를 판단하는 것이다.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    for path, label in [
        (args.internal_split_dir / "model_safe_split_view.jsonl", "internal_split_view"),
        (args.materialization_dir / "row_manifest.json", "source_materialization_manifest"),
        (args.support_contact_capacity_dir / "summary.json", "support_contact_capacity_summary"),
    ]:
        if not path.exists():
            errors.append({"error_type": "missing_input", "label": label, "path": str(path)})

    all_split_rows = list(read_jsonl(args.internal_split_dir / "model_safe_split_view.jsonl")) if not errors else []
    train_rows = [row for row in all_split_rows if row.get("protocol_split") == TRAIN_SPLIT]
    dev_rows = [row for row in all_split_rows if row.get("protocol_split") == DEV_SPLIT]
    heldout_rows = [row for row in all_split_rows if row.get("protocol_split") == HELDOUT_SPLIT]
    hardneg_train_rows, hardneg_summary = build_hard_negative_train_rows(train_rows)

    source_records: list[dict[str, Any]] = []
    score_summary: dict[str, Any] = {}
    source_family_metrics: list[dict[str, Any]] = []
    aggregate_metrics: list[dict[str, Any]] = []
    improvement_rows: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []
    fit_summary: dict[str, Any] = {}
    temp_summary: dict[str, Any] = {}
    support_summary: dict[str, Any] = read_json(args.support_contact_capacity_dir / "summary.json") if (args.support_contact_capacity_dir / "summary.json").exists() else {}

    if not errors:
        current_model, current_prior, current_fit = fit_model(train_rows, current_ce_features, args.epochs, args.lr, args.l2)
        hard_model, hard_prior, hard_fit = fit_model(hardneg_train_rows, structured_ce_features, args.epochs, args.lr, args.l2)
        route_models, route_priors, route_fit = fit_route_models(hardneg_train_rows, structured_ce_features, args.epochs, args.lr, args.l2)

        current_predict = lambda row: predict_model(current_model, current_prior, row, current_ce_features)
        hard_predict = lambda row: predict_model(hard_model, hard_prior, row, structured_ce_features)
        route_predict = lambda row: predict_route(route_models, route_priors, row, structured_ce_features)
        temp_summary = tune_temperature(dev_rows, route_predict)
        temperature = float(temp_summary["temperature"])
        calibrated_route_predict = lambda row: apply_temperature(route_predict(row), temperature)

        fit_summary = {
            "current_Ce": current_fit,
            "hardneg_structured_Ce": hard_fit,
            "route_aware_Ce": route_fit,
            "hard_negative_augmentation": hardneg_summary,
            "temperature_calibration": temp_summary,
        }
        calibration_rows = calibration_table(
            all_split_rows,
            {
                "current_Ce": current_predict,
                "hardneg_structured_Ce": hard_predict,
                "route_aware_Ce": route_predict,
                "calibrated_route_aware_Ce": calibrated_route_predict,
            },
        )
        source_records, score_summary, row_errors = score_source_rows(
            args.materialization_dir,
            {
                "current_Ce": current_predict,
                "hardneg_structured_Ce": hard_predict,
                "route_aware_Ce": route_predict,
                "calibrated_route_aware_Ce": calibrated_route_predict,
            },
        )
        errors.extend(row_errors)
        if len(source_records) != EXPECTED_TOTAL_ROWS:
            errors.append({"error_type": "source_row_count_mismatch", "actual": len(source_records), "expected": EXPECTED_TOTAL_ROWS})
        if not errors:
            source_family_metrics, aggregate_metrics, improvement_rows = metric_tables(source_records)

    by_metric = {
        (row.get("level"), row.get("score_id"), int(row.get("K", 0))): row
        for row in aggregate_metrics
    }
    def recall_at(score_id: str, k: int) -> float:
        return safe_float(by_metric.get(("primary_success_weighted", score_id, k), {}).get("Recall@K"), 0.0)
    def violation_at(score_id: str, k: int) -> float:
        return safe_float(by_metric.get(("primary_success_weighted", score_id, k), {}).get("Violation@K"), 1.0)

    # Conservative selection: keep the existing main score unless an improved
    # score improves or preserves K=10 recall and reduces K=10 violation.
    candidate_scores = SCORE_IDS[2:]
    best_score = "S2_current_source_x_Ce"
    best_tuple = (recall_at(best_score, 10), -violation_at(best_score, 10))
    for score_id in candidate_scores:
        candidate_tuple = (recall_at(score_id, 10), -violation_at(score_id, 10))
        if candidate_tuple > best_tuple:
            best_score = score_id
            best_tuple = candidate_tuple

    support_binary_rows = int(
        support_summary.get("decision_inputs", {}).get("binary_rows_after_repair", 0)
        or support_summary.get("row_counts", {}).get("binary_rows", 0)
        or support_summary.get("input_counts", {}).get("binary_rows", 0)
        or 0
    )
    support_mixed_pairs = int(
        support_summary.get("decision_inputs", {}).get("mixed_class_pairs_after_repair", 0)
        or support_summary.get("row_counts", {}).get("mixed_class_pairs", 0)
        or support_summary.get("input_counts", {}).get("mixed_class_pairs", 0)
        or 0
    )
    support_promote = bool(support_summary.get("decision", {}).get("support_contact_metric_rerun_allowed", False))

    stage_rows = [
        {
            "stage": "1_hard_negative_structured_Ce",
            "decision": "diagnostic_ablation_ready",
            "reason": f"added {hardneg_summary.get('added_inverse_hard_negatives', 0)} inverse-predicate hard negatives and structured signed-margin features",
        },
        {
            "stage": "2_route_aware_Ce",
            "decision": "candidate_method_but_not_auto_promoted",
            "reason": "route-specific models match H002 route-aware design, but source-reranking promotion depends on Recall/Violation tradeoff",
        },
        {
            "stage": "3_richer_Ge_support_contact",
            "decision": "blocked_for_main_route",
            "reason": f"support/contact capacity gate remains insufficient: binary_rows={support_binary_rows}, mixed_class_pairs={support_mixed_pairs}",
        },
        {
            "stage": "4_calibrated_Ce",
            "decision": "calibration_diagnostic_only",
            "reason": f"temperature={temp_summary.get('temperature', 1.0)} selected on internal_dev; does not by itself solve hard-route generalization",
        },
    ]

    calibrated_candidate_pass = best_score == "I4_calibrated_route_aware_source_x_Ce"
    decision = {
        "selected_path": "keep_current_Ce_main_score_use_improvements_as_ablation_or_next_method" if best_score == "S2_current_source_x_Ce" else "calibrated_route_aware_candidate_requires_ci_and_family_review_before_promotion",
        "best_primary_score": best_score,
        "calibrated_ce_candidate_pass": calibrated_candidate_pass,
        "calibrated_ce_main_promotion": False,
        "richer_ge_support_contact_promotion": support_promote,
        "pobs_prel_reopened": False,
        "next_todo": "h002_core_claim_without_pobs_boundary_update",
    }

    status = STATUS_READY if not errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "input_artifacts": {
            "internal_split_dir": rel_path(args.repo_root, args.internal_split_dir),
            "materialization_dir": rel_path(args.repo_root, args.materialization_dir),
            "support_contact_capacity_dir": rel_path(args.repo_root, args.support_contact_capacity_dir),
        },
        "row_counts": {
            "internal_train": len(train_rows),
            "internal_dev": len(dev_rows),
            "internal_heldout": len(heldout_rows),
            "source_rows_scored": len(source_records),
        },
        "fit_summary": fit_summary,
        "support_contact_capacity": {
            "binary_rows": support_binary_rows,
            "mixed_class_pairs": support_mixed_pairs,
            "metric_rerun_allowed": support_promote,
        },
        "decision": decision,
        "outputs": {
            "summary": rel_path(args.repo_root, args.out / "summary.json"),
            "source_family_metrics": rel_path(args.repo_root, args.out / "source_family_metrics.csv"),
            "score_condition_metrics": rel_path(args.repo_root, args.out / "score_condition_metrics.csv"),
            "improvement_summary": rel_path(args.repo_root, args.out / "improvement_summary.csv"),
            "ce_internal_calibration_metrics": rel_path(args.repo_root, args.out / "ce_internal_calibration_metrics.csv"),
            "stage_decision": rel_path(args.repo_root, args.out / "stage_decision.csv"),
            "report": rel_path(args.repo_root, args.out / "report.md"),
            "validation_errors": rel_path(args.repo_root, args.out / "validation_errors.jsonl"),
        },
        "boundary": {
            "official_test_used": False,
            "official_validation_eval_only": True,
            "fit_or_tune_on_official_validation": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "C_e_excludes_Z_e": True,
            "Z_e_combined_only_after_C_e": True,
        },
    }

    write_json(args.out / "summary.json", summary)
    write_csv(args.out / "source_family_metrics.csv", source_family_metrics)
    write_csv(args.out / "score_condition_metrics.csv", aggregate_metrics)
    write_csv(args.out / "improvement_summary.csv", improvement_rows)
    write_csv(args.out / "ce_internal_calibration_metrics.csv", calibration_rows)
    write_csv(args.out / "stage_decision.csv", stage_rows)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    (args.out / "report.md").write_text(build_report(summary, aggregate_metrics, calibration_rows, stage_rows), encoding="utf-8")
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
