#!/usr/bin/env python3
"""H001 family-wise metrics, paired CIs, and scale-robust fusion baselines."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "h001_reviewer_extension_metrics_v1"
FAMILIES = ("support_contact", "proximity", "relative_vertical")
KS = (5, 10, 20, 50, 100)
CONDITIONS = (
    "semantic_only",
    "family_conditional_risk",
    "pooled_calibration",
    "geometry_only_family",
    "rank_average_fusion",
    "reciprocal_rank_fusion",
    "loglinear_family_lambda_0_5",
    "loglinear_family_lambda_2_0",
)
SOURCE_SPECS = {
    "vlsat_closed_set": {
        "predictions": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl",
        "verification": "experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl",
        "ground_truth": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
    },
    "open3dsg_ov_recovery": {
        "predictions": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl",
        "verification": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl",
        "ground_truth": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/reviewer_extension_metrics/frozen_v1"),
    )
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260710)
    return parser.parse_args()


def resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def load_eval_module(repo_root: Path) -> Any:
    path = repo_root / "src/geocalib/evaluate_predictions.py"
    spec = importlib.util.spec_from_file_location("h001_eval", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_import:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prediction_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        row["scan_id"],
        int(row["subset_split_id"]),
        int(row["edge"]["subject_id"]),
        int(row["edge"]["object_id"]),
        row["predicate"]["predicate_label"],
    )


def gt_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        row["scan_id"],
        int(row["subset_split_id"]),
        int(row["subject_id"]),
        int(row["object_id"]),
        row["predicate_label"],
    )


def load_candidates(
    root: Path,
    source: str,
    spec: dict[str, str],
    evalmod: Any,
    family_model: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], int, int]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    prediction_path = resolve(root, spec["predictions"])
    verification_path = resolve(root, spec["verification"])
    input_count = 0
    with prediction_path.open("r", encoding="utf-8") as pred_handle, verification_path.open(
        "r", encoding="utf-8"
    ) as ver_handle:
        for line_no, (pred_line, ver_line) in enumerate(zip(pred_handle, ver_handle), 1):
            if not pred_line.strip() or not ver_line.strip():
                raise ValueError(f"blank_or_unaligned:{source}:{line_no}")
            pred = json.loads(pred_line)
            ver_raw = json.loads(ver_line)
            input_count += 1
            if pred["prediction_id"] != ver_raw["prediction_id"]:
                raise ValueError(f"prediction_verification_mismatch:{source}:{line_no}")
            family = pred["predicate"]["predicate_family"]
            if family not in FAMILIES:
                continue
            compact = evalmod.compact_verification(ver_raw)
            semantic = evalmod.semantic_score(pred)
            pooled = evalmod.p_geom_valid_from_verification(compact)
            family_probability = evalmod.family_specific_p_geom_valid(pred, compact, family_model)
            if semantic is None or pooled is None or family_probability is None:
                raise ValueError(f"missing_score:{source}:{pred['prediction_id']}")
            grouped[pred["subgraph_id"]].append(
                {
                    "prediction_id": pred["prediction_id"],
                    "key": prediction_key(pred),
                    "subgraph_id": pred["subgraph_id"],
                    "family": family,
                    "semantic": float(semantic),
                    "p_pooled": float(pooled),
                    "p_family": float(family_probability),
                    "status": compact.get("verification_status"),
                    "scores": {},
                }
            )
        if pred_handle.readline() or ver_handle.readline():
            raise ValueError(f"prediction_verification_length_mismatch:{source}")

    for candidates in grouped.values():
        semantic_order = sorted(candidates, key=lambda row: (-row["semantic"], row["key"]))
        geometry_order = sorted(candidates, key=lambda row: (-row["p_family"], row["key"]))
        semantic_rank = {row["prediction_id"]: rank for rank, row in enumerate(semantic_order, 1)}
        geometry_rank = {row["prediction_id"]: rank for rank, row in enumerate(geometry_order, 1)}
        denominator = max(len(candidates) - 1, 1)
        for row in candidates:
            rank_sem = semantic_rank[row["prediction_id"]]
            rank_geom = geometry_rank[row["prediction_id"]]
            percentile_sem = 1.0 - (rank_sem - 1) / denominator
            percentile_geom = 1.0 - (rank_geom - 1) / denominator
            row["scores"] = {
                "semantic_only": row["semantic"],
                "family_conditional_risk": row["semantic"] * row["p_family"],
                "pooled_calibration": row["semantic"] * row["p_pooled"],
                "geometry_only_family": row["p_family"],
                "rank_average_fusion": 0.5 * (percentile_sem + percentile_geom),
                "reciprocal_rank_fusion": 1.0 / (60.0 + rank_sem) + 1.0 / (60.0 + rank_geom),
                "loglinear_family_lambda_0_5": row["semantic"] * math.sqrt(max(row["p_family"], 0.0)),
                "loglinear_family_lambda_2_0": row["semantic"] * row["p_family"] ** 2,
            }
    in_scope = sum(len(rows) for rows in grouped.values())
    print(json.dumps({"source": source, "input_rows": input_count, "in_scope_rows": in_scope}))
    return grouped, input_count, in_scope


def load_gt(path: Path) -> tuple[dict[str, set[tuple[Any, ...]]], dict[str, dict[str, set[tuple[Any, ...]]]]]:
    overall: dict[str, set[tuple[Any, ...]]] = defaultdict(set)
    by_family: dict[str, dict[str, set[tuple[Any, ...]]]] = defaultdict(lambda: defaultdict(set))
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            family = row["predicate_family"]
            if family not in FAMILIES:
                continue
            key = gt_key(row)
            overall[row["subgraph_id"]].add(key)
            by_family[row["subgraph_id"]][family].add(key)
    return overall, by_family


def metric_values(
    selected: list[dict[str, Any]], gt: set[tuple[Any, ...]]
) -> tuple[float, float, float, float]:
    selected_keys = {row["key"] for row in selected}
    statuses = [row["status"] for row in selected if row["status"] in {"satisfied", "uncertain", "violated"}]
    return (
        float(len(selected_keys & gt)),
        float(len(gt)),
        float(sum(status == "violated" for status in statuses)),
        float(len(statuses)),
    )


def initialize_contribs(subgraphs: list[str]) -> dict[str, dict[str, dict[str, np.ndarray]]]:
    return {
        condition: {
            str(k): {
                "recall_num": np.zeros(len(subgraphs), dtype=np.float64),
                "recall_den": np.zeros(len(subgraphs), dtype=np.float64),
                "violation_num": np.zeros(len(subgraphs), dtype=np.float64),
                "violation_den": np.zeros(len(subgraphs), dtype=np.float64),
            }
            for k in KS
        }
        for condition in CONDITIONS
    }


def fill_scope_contributions(
    grouped: dict[str, list[dict[str, Any]]],
    gt_overall: dict[str, set[tuple[Any, ...]]],
    gt_family: dict[str, dict[str, set[tuple[Any, ...]]]],
    subgraphs: list[str],
) -> tuple[
    dict[str, dict[str, dict[str, np.ndarray]]],
    dict[str, dict[str, dict[str, dict[str, np.ndarray]]]],
    dict[str, dict[str, dict[str, dict[str, np.ndarray]]]],
]:
    overall = initialize_contribs(subgraphs)
    within_family = {family: initialize_contribs(subgraphs) for family in FAMILIES}
    global_family_slice = {family: initialize_contribs(subgraphs) for family in FAMILIES}
    for index, subgraph in enumerate(subgraphs):
        candidates = grouped.get(subgraph, [])
        for condition in CONDITIONS:
            ranked_global = sorted(candidates, key=lambda row: (-row["scores"][condition], row["key"]))
            ranked_family = {
                family: [row for row in ranked_global if row["family"] == family]
                for family in FAMILIES
            }
            for k in KS:
                global_selected = ranked_global[:k]
                values = metric_values(global_selected, gt_overall.get(subgraph, set()))
                for field, value in zip(("recall_num", "recall_den", "violation_num", "violation_den"), values):
                    overall[condition][str(k)][field][index] = value
                for family in FAMILIES:
                    family_gt = gt_family.get(subgraph, {}).get(family, set())
                    family_selected = ranked_family[family][:k]
                    values = metric_values(family_selected, family_gt)
                    for field, value in zip(("recall_num", "recall_den", "violation_num", "violation_den"), values):
                        within_family[family][condition][str(k)][field][index] = value
                    global_slice = [row for row in global_selected if row["family"] == family]
                    values = metric_values(global_slice, family_gt)
                    for field, value in zip(("recall_num", "recall_den", "violation_num", "violation_den"), values):
                        global_family_slice[family][condition][str(k)][field][index] = value
    return overall, within_family, global_family_slice


def summarize_contrib(
    contrib: dict[str, np.ndarray], sample_indices: np.ndarray
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for metric, numerator_field, denominator_field in (
        ("recall", "recall_num", "recall_den"),
        ("violation_rate", "violation_num", "violation_den"),
    ):
        numerator = contrib[numerator_field]
        denominator = contrib[denominator_field]
        point = float(numerator.sum() / denominator.sum()) if denominator.sum() > 0 else None
        sampled_num = numerator[sample_indices].sum(axis=1)
        sampled_den = denominator[sample_indices].sum(axis=1)
        samples = np.divide(
            sampled_num,
            sampled_den,
            out=np.full_like(sampled_num, np.nan),
            where=sampled_den > 0,
        )
        finite = samples[np.isfinite(samples)]
        ci = [float(value) for value in np.percentile(finite, [2.5, 97.5])] if len(finite) else [None, None]
        output[metric] = {
            "point": point,
            "ci95": ci,
            "numerator": int(numerator.sum()),
            "denominator": int(denominator.sum()),
            "bootstrap_samples": samples,
        }
    return output


def summarize_scope(
    contribs: dict[str, dict[str, dict[str, np.ndarray]]], sample_indices: np.ndarray
) -> tuple[dict[str, Any], dict[str, dict[str, dict[str, np.ndarray]]]]:
    summary: dict[str, Any] = {}
    samples: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    for condition in CONDITIONS:
        summary[condition] = {}
        samples[condition] = {}
        for k in KS:
            values = summarize_contrib(contribs[condition][str(k)], sample_indices)
            summary[condition][str(k)] = {}
            samples[condition][str(k)] = {}
            for metric in ("recall", "violation_rate"):
                samples[condition][str(k)][metric] = values[metric].pop("bootstrap_samples")
                summary[condition][str(k)][metric] = values[metric]
    for reference in ("semantic_only", "family_conditional_risk"):
        delta_key = f"deltas_vs_{reference}"
        summary[delta_key] = {}
        for condition in CONDITIONS:
            if condition == reference:
                continue
            summary[delta_key][condition] = {}
            for k in KS:
                summary[delta_key][condition][str(k)] = {}
                for metric in ("recall", "violation_rate"):
                    point = summary[condition][str(k)][metric]["point"] - summary[reference][str(k)][metric]["point"]
                    delta_samples = samples[condition][str(k)][metric] - samples[reference][str(k)][metric]
                    finite = delta_samples[np.isfinite(delta_samples)]
                    summary[delta_key][condition][str(k)][metric] = {
                        "point": point,
                        "ci95": [float(value) for value in np.percentile(finite, [2.5, 97.5])],
                        "prob_delta_le_zero": float(np.mean(finite <= 0.0)),
                        "prob_delta_ge_zero": float(np.mean(finite >= 0.0)),
                    }
    return summary, samples


def strip_arrays(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: strip_arrays(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [strip_arrays(value) for value in payload]
    if isinstance(payload, np.ndarray):
        return None
    return payload


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def make_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# H001 Reviewer-Extension Metrics",
        "",
        f"Status: `{report['status']}`",
        f"Bootstrap: `{report['n_bootstrap']}` paired subgraph resamples",
        "",
        "`rank_average_fusion` and `reciprocal_rank_fusion` are fixed, parameter-free, scale-robust late-fusion baselines. They are comparisons, not newly selected main scores.",
        "",
        "## Overall global in-scope ranking",
        "",
        "| source | condition | K | R@K | R 95% CI | V@K | V 95% CI | dR vs semantic | dV vs semantic |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source, source_data in report["sources"].items():
        scope = source_data["overall_global"]
        for condition in CONDITIONS:
            for k in KS:
                row = scope[condition][str(k)]
                delta = scope["deltas_vs_semantic_only"].get(condition, {}).get(str(k), {})
                lines.append(
                    f"| {source} | {condition} | {k} | {fmt(row['recall']['point'])} | {row['recall']['ci95']} | {fmt(row['violation_rate']['point'])} | {row['violation_rate']['ci95']} | {fmt(delta.get('recall', {}).get('point'))} | {fmt(delta.get('violation_rate', {}).get('point'))} |"
                )
    lines.extend(
        [
            "",
            "## Family-wise outputs",
            "",
            "`family_metrics.csv` contains within-family top-K recall/violation with paired CIs. `global_topk_family_slice.csv` reports each family's contribution inside the actual global top-K list.",
            "",
            "The violation target in this label-free table is still the frozen geometry verifier. The independent human audit evaluator is the non-circular primary check once labels are available.",
            "",
        ]
    )
    return "\n".join(lines)


def csv_rows(report: dict[str, Any], scope_name: str) -> list[dict[str, Any]]:
    output = []
    for source, source_data in report["sources"].items():
        for family in FAMILIES:
            scope = source_data[scope_name][family]
            for condition in CONDITIONS:
                for k in KS:
                    value = scope[condition][str(k)]
                    delta = scope["deltas_vs_semantic_only"].get(condition, {}).get(str(k), {})
                    delta_main = scope["deltas_vs_family_conditional_risk"].get(condition, {}).get(str(k), {})
                    output.append(
                        {
                            "source": source,
                            "scope": scope_name,
                            "family": family,
                            "condition": condition,
                            "k": k,
                            "recall": value["recall"]["point"],
                            "recall_ci95_low": value["recall"]["ci95"][0],
                            "recall_ci95_high": value["recall"]["ci95"][1],
                            "violation_rate": value["violation_rate"]["point"],
                            "violation_ci95_low": value["violation_rate"]["ci95"][0],
                            "violation_ci95_high": value["violation_rate"]["ci95"][1],
                            "delta_recall_vs_semantic": delta.get("recall", {}).get("point"),
                            "delta_violation_vs_semantic": delta.get("violation_rate", {}).get("point"),
                            "delta_recall_vs_main": delta_main.get("recall", {}).get("point"),
                            "delta_recall_vs_main_ci95_low": (delta_main.get("recall", {}).get("ci95") or [None, None])[0],
                            "delta_recall_vs_main_ci95_high": (delta_main.get("recall", {}).get("ci95") or [None, None])[1],
                            "delta_violation_vs_main": delta_main.get("violation_rate", {}).get("point"),
                            "delta_violation_vs_main_ci95_low": (delta_main.get("violation_rate", {}).get("ci95") or [None, None])[0],
                            "delta_violation_vs_main_ci95_high": (delta_main.get("violation_rate", {}).get("ci95") or [None, None])[1],
                            "selected_or_correct_numerator": value["violation_rate"]["numerator"],
                            "violation_denominator": value["violation_rate"]["denominator"],
                        }
                    )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = resolve(root, args.out)
    evalmod = load_eval_module(root)
    family_model_path = root / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json"
    family_model = read_json(family_model_path)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_label_free_verifier_diagnostic",
        "n_bootstrap": args.n_bootstrap,
        "seed": args.seed,
        "bootstrap_unit": "subgraph_id",
        "conditions": list(CONDITIONS),
        "condition_definitions": {
            "semantic_only": "semantic_score",
            "family_conditional_risk": "semantic_score * p_geom_valid_family (locked main score)",
            "pooled_calibration": "semantic_score * p_geom_valid_pooled",
            "geometry_only_family": "p_geom_valid_family",
            "rank_average_fusion": "mean(global within-subgraph semantic percentile, family-geometry percentile)",
            "reciprocal_rank_fusion": "1/(60+semantic_rank) + 1/(60+family_geometry_rank)",
            "loglinear_family_lambda_0_5": "semantic_score * p_geom_valid_family^0.5 (fixed sensitivity)",
            "loglinear_family_lambda_2_0": "semantic_score * p_geom_valid_family^2 (fixed sensitivity)",
        },
        "sources": {},
        "limitations": [
            "Violation labels in this artifact are verifier-derived and therefore diagnostic, not independent human validity.",
            "Fusion baselines were fixed before this run and are not promoted based on the resulting validation values.",
        ],
    }
    for source_index, (source, spec) in enumerate(SOURCE_SPECS.items()):
        grouped, input_count, in_scope = load_candidates(root, source, spec, evalmod, family_model)
        gt_overall, gt_family = load_gt(resolve(root, spec["ground_truth"]))
        subgraphs = sorted(set(grouped) | set(gt_overall))
        rng = np.random.default_rng(args.seed + source_index)
        sample_indices = rng.integers(0, len(subgraphs), size=(args.n_bootstrap, len(subgraphs)))
        overall_contrib, within_contrib, slice_contrib = fill_scope_contributions(
            grouped, gt_overall, gt_family, subgraphs
        )
        overall_summary, _ = summarize_scope(overall_contrib, sample_indices)
        within_summary = {family: summarize_scope(within_contrib[family], sample_indices)[0] for family in FAMILIES}
        slice_summary = {family: summarize_scope(slice_contrib[family], sample_indices)[0] for family in FAMILIES}
        report["sources"][source] = {
            "input_rows": input_count,
            "in_scope_rows": in_scope,
            "subgraphs": len(subgraphs),
            "overall_global": strip_arrays(overall_summary),
            "within_family": strip_arrays(within_summary),
            "global_topk_family_slice": strip_arrays(slice_summary),
            "inputs": {key: value for key, value in spec.items()},
        }
        del grouped

    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "summary.json", report)
    (out / "summary.md").write_text(make_markdown(report), encoding="utf-8")
    write_csv(out / "family_metrics.csv", csv_rows(report, "within_family"))
    write_csv(out / "global_topk_family_slice.csv", csv_rows(report, "global_topk_family_slice"))
    write_json(
        out / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": report["created_at_utc"],
            "status": report["status"],
            "outputs": [
                relpath(root, out / "summary.json"),
                relpath(root, out / "summary.md"),
                relpath(root, out / "family_metrics.csv"),
                relpath(root, out / "global_topk_family_slice.csv"),
            ],
            "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm reviewer_extension_metrics",
        },
    )
    print(json.dumps({"status": report["status"], "sources": list(report["sources"]), "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
