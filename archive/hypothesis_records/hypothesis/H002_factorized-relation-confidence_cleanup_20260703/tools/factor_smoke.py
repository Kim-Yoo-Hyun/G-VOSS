#!/usr/bin/env python3
"""Train-only H002 factorized reliability smoke baselines."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_DATASET_DIR = RGA_ROOT / "factor_dataset"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "factor_smoke"

BASELINES = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
]

PROBE_NAMES = [
    "semantic_score_norm",
    "negative_semantic_score_norm",
    "p_geom_valid",
    "geometry_satisfied_rule",
    "rga_shortcut_rule",
]

TARGET_FILES = {
    "strict": "strict_smoke.jsonl",
    "weak": "weak_smoke.jsonl",
}

SHORTCUT_KEYS = {
    "top100_and_unsatisfied",
    "tail_gt100_and_satisfied",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(value) or math.isinf(value):
        return default
    return value


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def target_y(row: dict[str, Any]) -> int:
    y = row["target"]["y"]
    if y not in {0, 1}:
        raise ValueError(f"expected binary target, got {y!r}")
    return int(y)


def target_weight(row: dict[str, Any]) -> float:
    return safe_float(row["target"].get("sample_weight"), 1.0)


def identity_key(row: dict[str, Any]) -> str:
    return str(row["identity"]["prediction_id"])


def split_feature_types(rows: list[dict[str, Any]], baseline: str) -> dict[str, Any]:
    numeric: set[str] = set()
    categorical_values: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for key, value in row["baseline_inputs"][baseline].items():
            if key in SHORTCUT_KEYS:
                pass
            if isinstance(value, (int, float, bool)) or value is None:
                numeric.add(key)
            else:
                categorical_values[key].add(str(value))
    return {
        "numeric": sorted(numeric),
        "categorical": {key: sorted(values) for key, values in sorted(categorical_values.items())},
    }


def vector_names(schema: dict[str, Any]) -> list[str]:
    names = list(schema["numeric"])
    for key, values in schema["categorical"].items():
        names.extend(f"{key}={value}" for value in values)
    return names


def vectorize_one(row: dict[str, Any], baseline: str, schema: dict[str, Any]) -> list[float]:
    features = row["baseline_inputs"][baseline]
    values: list[float] = []
    for key in schema["numeric"]:
        values.append(safe_float(features.get(key), 0.0))
    for key, categories in schema["categorical"].items():
        observed = str(features.get(key))
        values.extend(1.0 if observed == category else 0.0 for category in categories)
    return values


def vectorize(rows: list[dict[str, Any]], baseline: str, schema: dict[str, Any]) -> list[list[float]]:
    return [vectorize_one(row, baseline, schema) for row in rows]


def fit_scaler(xs: list[list[float]]) -> tuple[list[float], list[float]]:
    if not xs:
        return [], []
    dims = len(xs[0])
    means = [0.0] * dims
    for row in xs:
        for idx, value in enumerate(row):
            means[idx] += value
    means = [value / len(xs) for value in means]
    variances = [0.0] * dims
    for row in xs:
        for idx, value in enumerate(row):
            diff = value - means[idx]
            variances[idx] += diff * diff
    stds = []
    for value in variances:
        std = math.sqrt(value / len(xs))
        stds.append(std if std > 1e-12 else 1.0)
    return means, stds


def apply_scaler(xs: list[list[float]], means: list[float], stds: list[float]) -> list[list[float]]:
    return [[(value - means[idx]) / stds[idx] for idx, value in enumerate(row)] for row in xs]


def fit_logistic(
    xs: list[list[float]],
    ys: list[int],
    sample_weights: list[float],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> list[float]:
    if not xs:
        raise ValueError("empty training matrix")
    dims = len(xs[0])
    weights = [0.0] * (dims + 1)
    weight_sum = sum(sample_weights) or float(len(xs))
    positive_rate = sum(y * w for y, w in zip(ys, sample_weights)) / weight_sum
    positive_rate = min(max(positive_rate, 1e-4), 1.0 - 1e-4)
    weights[0] = math.log(positive_rate / (1.0 - positive_rate))

    for epoch in range(epochs):
        rate = learning_rate / math.sqrt(1.0 + epoch / 200.0)
        gradients = [0.0] * (dims + 1)
        for row, y, sample_weight in zip(xs, ys, sample_weights):
            logit = weights[0]
            for idx, value in enumerate(row):
                logit += weights[idx + 1] * value
            pred = sigmoid(logit)
            error = (pred - y) * sample_weight
            gradients[0] += error
            for idx, value in enumerate(row):
                gradients[idx + 1] += error * value
        gradients[0] /= weight_sum
        for idx in range(dims):
            gradients[idx + 1] = gradients[idx + 1] / weight_sum + l2 * weights[idx + 1]
        for idx, gradient in enumerate(gradients):
            weights[idx] -= rate * gradient
    return weights


def predict_probs(xs: list[list[float]], weights: list[float]) -> list[float]:
    scores = []
    for row in xs:
        logit = weights[0]
        for idx, value in enumerate(row):
            logit += weights[idx + 1] * value
        scores.append(sigmoid(logit))
    return scores


def auroc(ys: list[int], scores: list[float]) -> float | None:
    positives = [score for y, score in zip(ys, scores) if y == 1]
    negatives = [score for y, score in zip(ys, scores) if y == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    total = len(positives) * len(negatives)
    for positive_score in positives:
        for negative_score in negatives:
            if positive_score > negative_score:
                wins += 1.0
            elif positive_score == negative_score:
                wins += 0.5
    return wins / total


def auprc(ys: list[int], scores: list[float]) -> float | None:
    positives = sum(ys)
    if positives == 0:
        return None
    pairs = sorted(zip(scores, ys), key=lambda item: item[0], reverse=True)
    true_positive = 0
    precision_sum = 0.0
    for rank, (_, y) in enumerate(pairs, start=1):
        if y == 1:
            true_positive += 1
            precision_sum += true_positive / rank
    return precision_sum / positives


def ece(ys: list[int], probs: list[float], bins: int = 5) -> float:
    if not ys:
        return 0.0
    total = len(ys)
    accum = 0.0
    for bin_idx in range(bins):
        left = bin_idx / bins
        right = (bin_idx + 1) / bins
        selected = [
            (y, p)
            for y, p in zip(ys, probs)
            if (left <= p < right) or (bin_idx == bins - 1 and p == 1.0)
        ]
        if not selected:
            continue
        acc = sum(y for y, _ in selected) / len(selected)
        conf = sum(p for _, p in selected) / len(selected)
        accum += len(selected) / total * abs(acc - conf)
    return accum


def metrics(ys: list[int], probs: list[float]) -> dict[str, Any]:
    eps = 1e-12
    y_count = Counter(ys)
    predictions = [1 if prob >= 0.5 else 0 for prob in probs]
    accuracy = sum(1 for y, pred in zip(ys, predictions) if y == pred) / len(ys)
    brier = sum((prob - y) ** 2 for y, prob in zip(ys, probs)) / len(ys)
    nll = -sum(y * math.log(max(prob, eps)) + (1 - y) * math.log(max(1 - prob, eps)) for y, prob in zip(ys, probs)) / len(ys)
    return {
        "rows": len(ys),
        "positive": y_count[1],
        "negative": y_count[0],
        "auroc": auroc(ys, probs),
        "auprc": auprc(ys, probs),
        "brier": brier,
        "ece_5bin": ece(ys, probs, bins=5),
        "nll": nll,
        "accuracy_at_0_5": accuracy,
    }


def stratified_folds(rows: list[dict[str, Any]], fold_count: int) -> list[list[int]]:
    fold_count = max(2, min(fold_count, len(rows)))
    by_label: dict[int, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        by_label[target_y(row)].append(idx)
    folds = [[] for _ in range(fold_count)]
    for label in sorted(by_label):
        for offset, idx in enumerate(sorted(by_label[label], key=lambda i: identity_key(rows[i]))):
            folds[offset % fold_count].append(idx)
    return folds


def train_predict_in_sample(
    rows: list[dict[str, Any]],
    baseline: str,
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], dict[str, Any]]:
    schema = split_feature_types(rows, baseline)
    raw_xs = vectorize(rows, baseline, schema)
    means, stds = fit_scaler(raw_xs)
    xs = apply_scaler(raw_xs, means, stds)
    ys = [target_y(row) for row in rows]
    sample_weights = [target_weight(row) for row in rows]
    weights = fit_logistic(xs, ys, sample_weights, epochs=epochs, learning_rate=learning_rate, l2=l2)
    probs = predict_probs(xs, weights)
    return probs, {
        "feature_count": len(vector_names(schema)),
        "numeric_feature_count": len(schema["numeric"]),
        "categorical_feature_count": sum(len(values) for values in schema["categorical"].values()),
    }


def train_predict_crossfit(
    rows: list[dict[str, Any]],
    baseline: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], dict[str, Any]]:
    fold_indices = stratified_folds(rows, folds)
    all_probs = [0.5] * len(rows)
    feature_counts = []
    for test_indices in fold_indices:
        test_index_set = set(test_indices)
        train_rows = [row for idx, row in enumerate(rows) if idx not in test_index_set]
        test_rows = [rows[idx] for idx in test_indices]
        schema = split_feature_types(train_rows, baseline)
        train_raw = vectorize(train_rows, baseline, schema)
        test_raw = vectorize(test_rows, baseline, schema)
        means, stds = fit_scaler(train_raw)
        train_xs = apply_scaler(train_raw, means, stds)
        test_xs = apply_scaler(test_raw, means, stds)
        train_ys = [target_y(row) for row in train_rows]
        train_weights = [target_weight(row) for row in train_rows]
        weights = fit_logistic(train_xs, train_ys, train_weights, epochs=epochs, learning_rate=learning_rate, l2=l2)
        probs = predict_probs(test_xs, weights)
        for idx, prob in zip(test_indices, probs):
            all_probs[idx] = prob
        feature_counts.append(len(vector_names(schema)))
    return all_probs, {
        "fold_count": len(fold_indices),
        "fold_sizes": [len(indices) for indices in fold_indices],
        "feature_count_min": min(feature_counts),
        "feature_count_max": max(feature_counts),
    }


def probe_scores(rows: list[dict[str, Any]], probe_name: str) -> list[float]:
    scores = []
    for row in rows:
        baseline = row["baseline_inputs"]["factorized_reliability_posterior"]
        semantic = safe_float(baseline.get("semantic_score_norm"), 0.0)
        p_geom = safe_float(baseline.get("p_geom_valid_imputed_neutral"), 0.5)
        if probe_name == "semantic_score_norm":
            score = semantic
        elif probe_name == "negative_semantic_score_norm":
            score = 1.0 - semantic
        elif probe_name == "p_geom_valid":
            score = p_geom
        elif probe_name == "geometry_satisfied_rule":
            score = 1.0 if baseline.get("geometry_status") == "satisfied" else 0.0
        elif probe_name == "rga_shortcut_rule":
            if baseline.get("tail_gt100_and_satisfied") == 1:
                score = 1.0
            elif baseline.get("top100_and_unsatisfied") == 1:
                score = 0.0
            else:
                score = p_geom
        else:
            raise ValueError(f"unknown probe: {probe_name}")
        scores.append(score)
    return scores


def shortcut_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    family_counts = Counter()
    label_counts = Counter()
    for row in rows:
        y = target_y(row)
        baseline = row["baseline_inputs"]["factorized_reliability_posterior"]
        key = (
            y,
            int(baseline.get("top100_and_unsatisfied") or 0),
            int(baseline.get("tail_gt100_and_satisfied") or 0),
            str(baseline.get("geometry_status")),
        )
        counts[key] += 1
        family_counts[(y, str(baseline.get("predicate_family")))] += 1
        label_counts[(y, str(row["target"].get("working_label")))] += 1
    return {
        "target_shortcut_counts": [
            {
                "y": key[0],
                "top100_and_unsatisfied": key[1],
                "tail_gt100_and_satisfied": key[2],
                "geometry_status": key[3],
                "rows": value,
            }
            for key, value in sorted(counts.items())
        ],
        "target_family_counts": [
            {"y": key[0], "predicate_family": key[1], "rows": value}
            for key, value in sorted(family_counts.items())
        ],
        "target_working_label_counts": [
            {"y": key[0], "working_label": key[1], "rows": value}
            for key, value in sorted(label_counts.items())
        ],
    }


def build_prediction_rows(
    rows: list[dict[str, Any]],
    target_mode: str,
    split_eval: str,
    baseline: str,
    probs: list[float],
) -> list[dict[str, Any]]:
    outputs = []
    for row, prob in zip(rows, probs):
        outputs.append(
            {
                "schema_version": "h002_factor_smoke_prediction_v0",
                "target_mode": target_mode,
                "split_eval": split_eval,
                "baseline": baseline,
                "prediction_id": row["identity"]["prediction_id"],
                "scan_id": row["identity"]["scan_id"],
                "predicate_label": row["identity"]["predicate_label"],
                "predicate_family": row["identity"]["predicate_family"],
                "y": target_y(row),
                "score": prob,
                "working_label": row["target"].get("working_label"),
                "boundary": "train-only hypothesis-stage smoke; not paper metric",
            }
        )
    return outputs


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Factor Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage smoke.",
        "- No validation/test rows are used.",
        "- Working labels are machine-assisted, not paper-locked human labels.",
        "- Results are not paper-level metrics.",
        "",
        "## Main Metrics",
        "",
        "| Target | Eval | Baseline | Rows | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["kind"] != "baseline":
            continue
        m = row["metrics"]
        lines.append(
            "| {target_mode} | {split_eval} | {name} | {rows} | {auroc:.4f} | {auprc:.4f} | {brier:.4f} | {ece:.4f} | {acc:.4f} |".format(
                target_mode=row["target_mode"],
                split_eval=row["split_eval"],
                name=row["name"],
                rows=m["rows"],
                auroc=m["auroc"] if m["auroc"] is not None else float("nan"),
                auprc=m["auprc"] if m["auprc"] is not None else float("nan"),
                brier=m["brier"],
                ece=m["ece_5bin"],
                acc=m["accuracy_at_0_5"],
            )
        )
    lines.extend(
        [
            "",
            "## Probe Metrics",
            "",
            "| Target | Probe | AUROC | AUPRC | Brier | ECE-5 |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "probe":
            continue
        m = row["metrics"]
        lines.append(
            "| {target_mode} | {name} | {auroc:.4f} | {auprc:.4f} | {brier:.4f} | {ece:.4f} |".format(
                target_mode=row["target_mode"],
                name=row["name"],
                auroc=m["auroc"] if m["auroc"] is not None else float("nan"),
                auprc=m["auprc"] if m["auprc"] is not None else float("nan"),
                brier=m["brier"],
                ece=m["ece_5bin"],
            )
        )
    lines.extend(
        [
            "",
            "## Shortcut Caveat",
            "",
            "The strict target is almost a direct HL-vs-LH contrast. Therefore high smoke",
            "performance can reflect target construction shortcuts, not a validated",
            "relation reliability posterior.",
            "",
            "Next gate: `28_shortcut_control.md`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = as_abs(args.dataset_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows: list[dict[str, Any]] = []
    prediction_paths: dict[str, str] = {}
    shortcut_audits: dict[str, Any] = {}
    feature_summaries: dict[str, Any] = {}

    for target_mode, filename in TARGET_FILES.items():
        rows = read_jsonl(dataset_dir / filename)
        ys = [target_y(row) for row in rows]
        shortcut_audits[target_mode] = shortcut_audit(rows)
        for baseline in BASELINES:
            in_probs, in_feature_summary = train_predict_in_sample(
                rows,
                baseline,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            cross_probs, cross_feature_summary = train_predict_crossfit(
                rows,
                baseline,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[f"{target_mode}:{baseline}"] = {
                "in_sample": in_feature_summary,
                "crossfit": cross_feature_summary,
            }
            for split_eval, probs in [("in_sample", in_probs), ("train_internal_5fold", cross_probs)]:
                metric_rows.append(
                    {
                        "kind": "baseline",
                        "target_mode": target_mode,
                        "split_eval": split_eval,
                        "name": baseline,
                        "metrics": metrics(ys, probs),
                    }
                )
                pred_path = output_dir / f"predictions_{target_mode}_{split_eval}_{baseline}.jsonl"
                write_jsonl(pred_path, build_prediction_rows(rows, target_mode, split_eval, baseline, probs))
                prediction_paths[f"{target_mode}:{split_eval}:{baseline}"] = rel_path(pred_path) or str(pred_path)
        for probe_name in PROBE_NAMES:
            scores = probe_scores(rows, probe_name)
            metric_rows.append(
                {
                    "kind": "probe",
                    "target_mode": target_mode,
                    "split_eval": "score_probe",
                    "name": probe_name,
                    "metrics": metrics(ys, scores),
                }
            )

    summary = {
        "schema_version": "h002_factor_smoke_v0",
        "status": "ready_with_shortcut_caveat",
        "created_at": created_at,
        "input_paths": {
            target_mode: rel_path(dataset_dir / filename) for target_mode, filename in TARGET_FILES.items()
        },
        "output_dir": rel_path(output_dir),
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "tuned_on_validation": False,
            "uses_validation_rows": False,
        },
        "boundary": {
            "split": "train_only",
            "not_paper_result": True,
            "target_labels_are_machine_assisted": True,
            "human_confirmed": False,
            "label_evidence_as_input": False,
            "shortcut_caveat": True,
        },
        "metric_rows": metric_rows,
        "shortcut_audits": shortcut_audits,
        "feature_summaries": feature_summaries,
        "prediction_paths": prediction_paths,
    }

    summary_path = output_dir / "summary.json"
    metrics_path = output_dir / "metrics.csv"
    report_path = output_dir / "report.md"
    write_json(summary_path, summary)
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "kind",
                "target_mode",
                "split_eval",
                "name",
                "rows",
                "positive",
                "negative",
                "auroc",
                "auprc",
                "brier",
                "ece_5bin",
                "nll",
                "accuracy_at_0_5",
            ],
        )
        writer.writeheader()
        for row in metric_rows:
            flat = {
                "kind": row["kind"],
                "target_mode": row["target_mode"],
                "split_eval": row["split_eval"],
                "name": row["name"],
                **row["metrics"],
            }
            writer.writerow(flat)
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} output={summary['output_dir']} "
        f"metrics={len(summary['metric_rows'])} validation_used={summary['hyperparameters']['uses_validation_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
