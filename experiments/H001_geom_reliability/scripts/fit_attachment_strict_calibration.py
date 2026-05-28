#!/usr/bin/env python3
"""Fit attachment-deferred p_geom_valid from the frozen strict filter.

This G5 step fits a pooled attachment-deferred calibration model from G4c strict
rows. It does not score VL-SAT/Open3DSG source predictions, compute source
metrics, run controls/bootstrap, or change the main AAAI claim.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_attachment_deferred_calibration_fit_v1"
MODEL_SCHEMA_VERSION = "h001_attachment_deferred_p_geom_valid_model_v1"
METRICS_SCHEMA_VERSION = "h001_attachment_deferred_p_geom_valid_metrics_v1"
SCORE_SCHEMA_VERSION = "h001_attachment_deferred_p_geom_valid_score_v1"
STATUS = "attachment_deferred_calibration_fit_ready_no_source_metrics"
DEFAULT_ATTACHMENT_ROOT = Path("experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_STRICT_DIR = DEFAULT_ATTACHMENT_ROOT / "strict_filter_freeze"
DEFAULT_GT_POLICY_DIR = DEFAULT_ATTACHMENT_ROOT / "gt_policy_smoke"
DEFAULT_OUT = DEFAULT_ATTACHMENT_ROOT / "calibration_fit"

NUMERIC_FEATURES = (
    "min_point_distance_m",
    "log_near_contact_point_count",
    "contact_patch_score",
    "surface_candidate_count",
    "surface_distance_m",
    "surface_projected_overlap_ratio",
    "distance_3d_m",
    "distance_xy_m",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "center_delta_z_m",
    "abs_center_delta_z_m",
    "vertical_gap_m",
    "abs_vertical_gap_m",
    "projected_xy_overlap",
    "floor_clearance_m",
    "hanging_geometry_score",
    "support_explanation_score",
    "near_vertical_or_overhead_surface",
    "floor_or_table_supported",
    "surface_type_matches_attachment",
    "surface_normal_matches_attachment",
    "class_pair_prior_plausible",
)
CATEGORICAL_FIELDS = (
    "predicate_label",
    "subtype_hint",
    "surface_type",
    "surface_normal_class",
    "class_pair_prior",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--strict-filter-dir", type=Path, default=DEFAULT_STRICT_DIR)
    parser.add_argument("--gt-policy-dir", type=Path, default=DEFAULT_GT_POLICY_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--epochs", type=int, default=800)
    parser.add_argument("--learning-rate", type=float, default=0.15)
    parser.add_argument("--l2", type=float, default=1e-4)
    parser.add_argument("--bins", type=int, default=10)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def finite_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return default


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def dot(weights: list[float], vector: list[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, vector))


def log_loss(predictions: list[float], labels: list[int]) -> float | None:
    if not labels:
        return None
    eps = 1e-12
    total = 0.0
    for prob, label in zip(predictions, labels):
        prob = min(max(prob, eps), 1.0 - eps)
        total -= label * math.log(prob) + (1 - label) * math.log(1.0 - prob)
    return total / len(labels)


def brier_score(predictions: list[float], labels: list[int]) -> float | None:
    if not labels:
        return None
    return sum((prob - label) ** 2 for prob, label in zip(predictions, labels)) / len(labels)


def auroc(predictions: list[float], labels: list[int]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    pairs = sorted(zip(predictions, labels), key=lambda item: item[0])
    rank_sum = 0.0
    index = 0
    while index < len(pairs):
        next_index = index + 1
        while next_index < len(pairs) and pairs[next_index][0] == pairs[index][0]:
            next_index += 1
        avg_rank = (index + 1 + next_index) / 2.0
        positives_in_tie = sum(label for _, label in pairs[index:next_index])
        rank_sum += positives_in_tie * avg_rank
        index = next_index
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def average_precision(predictions: list[float], labels: list[int]) -> float | None:
    positives = sum(labels)
    if positives == 0:
        return None
    ranked = sorted(zip(predictions, labels), key=lambda item: item[0], reverse=True)
    true_positive = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(ranked, 1):
        if label == 1:
            true_positive += 1
            precision_sum += true_positive / rank
    return precision_sum / positives


def calibration_bins(
    predictions: list[float],
    labels: list[int],
    bins: int,
) -> tuple[list[dict[str, Any]], float | None, float | None]:
    if not labels:
        return [], None, None
    groups = [
        {"bin": index, "lower": index / bins, "upper": (index + 1) / bins, "count": 0}
        for index in range(bins)
    ]
    for prob, label in zip(predictions, labels):
        index = min(int(prob * bins), bins - 1)
        group = groups[index]
        group["count"] += 1
        group["prob_sum"] = group.get("prob_sum", 0.0) + prob
        group["label_sum"] = group.get("label_sum", 0.0) + label
    ece = 0.0
    mce = 0.0
    for group in groups:
        count = group["count"]
        if count:
            avg_conf = group["prob_sum"] / count
            empirical = group["label_sum"] / count
            gap = abs(avg_conf - empirical)
            group["avg_p_geom_valid"] = avg_conf
            group["empirical_geom_valid"] = empirical
            group["gap"] = gap
            ece += (count / len(labels)) * gap
            mce = max(mce, gap)
        else:
            group["avg_p_geom_valid"] = None
            group["empirical_geom_valid"] = None
            group["gap"] = None
        group.pop("prob_sum", None)
        group.pop("label_sum", None)
    return groups, ece, mce


def invalid_precision(predictions: list[float], labels: list[int]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for threshold in (0.1, 0.2, 0.3, 0.5):
        selected = [(prob, label) for prob, label in zip(predictions, labels) if prob <= threshold]
        invalid = sum(1 for _, label in selected if label == 0)
        result[str(threshold)] = {
            "selected": len(selected),
            "invalid": invalid,
            "precision_invalid": invalid / len(selected) if selected else None,
            "coverage": len(selected) / len(labels) if labels else None,
        }
    return result


def fit_logistic(
    vectors: list[list[float]],
    labels: list[int],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], list[dict[str, float]]]:
    weights = [0.0] * len(vectors[0])
    trace: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        gradients = [0.0] * len(weights)
        predictions: list[float] = []
        for vector, label in zip(vectors, labels):
            probability = sigmoid(dot(weights, vector))
            predictions.append(probability)
            error = probability - label
            for index, value in enumerate(vector):
                gradients[index] += error * value
        count = float(len(labels))
        for index in range(len(weights)):
            gradients[index] /= count
            if index != 0:
                gradients[index] += l2 * weights[index]
            weights[index] -= learning_rate * gradients[index]
        if epoch == 1 or epoch % 50 == 0 or epoch == epochs:
            loss = log_loss(predictions, labels) or 0.0
            penalty = 0.5 * l2 * sum(weight * weight for weight in weights[1:])
            trace.append({"epoch": epoch, "train_nll": loss + penalty})
    return weights, trace


def predict(vectors: list[list[float]], weights: list[float]) -> list[float]:
    return [sigmoid(dot(weights, vector)) for vector in vectors]


def is_attachment_surface(surface_type: str, normal_class: str) -> float:
    if surface_type in {"wall", "ceiling", "furniture", "fixture"}:
        return 1.0
    if normal_class in {"vertical", "horizontal_down"}:
        return 1.0
    return 0.0


def is_attachment_normal(normal_class: str) -> float:
    return 1.0 if normal_class in {"vertical", "horizontal_down", "slanted"} else 0.0


def evidence_features(evidence: dict[str, Any]) -> dict[str, float | str]:
    point = evidence.get("point_contact_evidence", {})
    surface = evidence.get("surface_evidence", {})
    selected = surface.get("candidates", [{}])[0] if surface.get("candidates") else {}
    obb = evidence.get("obb_evidence", {})
    gravity = evidence.get("gravity_evidence", {})
    support = evidence.get("contradictory_support_evidence", {})
    affordance = evidence.get("affordance_context", {})
    surface_type = str(surface.get("selected_surface_type") or "unknown")
    normal_class = str(surface.get("selected_surface_normal_class") or "unknown")
    class_prior = str(affordance.get("class_pair_prior") or "unknown")
    values: dict[str, float | str] = {
        "min_point_distance_m": finite_float(point.get("min_point_distance_m"), 10.0),
        "log_near_contact_point_count": math.log1p(finite_float(point.get("near_contact_point_count"))),
        "contact_patch_score": finite_float(point.get("contact_patch_score")),
        "surface_candidate_count": finite_float(surface.get("candidate_count")),
        "surface_distance_m": finite_float(selected.get("distance_m"), 10.0),
        "surface_projected_overlap_ratio": finite_float(selected.get("projected_overlap_ratio")),
        "distance_3d_m": finite_float(obb.get("distance_3d_m"), 10.0),
        "distance_xy_m": finite_float(obb.get("distance_xy_m"), 10.0),
        "normalized_distance_3d": finite_float(obb.get("normalized_distance_3d"), 10.0),
        "normalized_distance_xy": finite_float(obb.get("normalized_distance_xy"), 10.0),
        "center_delta_z_m": finite_float(obb.get("center_delta_z_m")),
        "abs_center_delta_z_m": abs(finite_float(obb.get("center_delta_z_m"))),
        "vertical_gap_m": finite_float(obb.get("vertical_gap_m")),
        "abs_vertical_gap_m": abs(finite_float(obb.get("vertical_gap_m"))),
        "projected_xy_overlap": finite_float(obb.get("projected_xy_overlap")),
        "floor_clearance_m": finite_float(gravity.get("floor_clearance_m")),
        "hanging_geometry_score": finite_float(gravity.get("hanging_geometry_score")),
        "support_explanation_score": finite_float(support.get("support_explanation_score")),
        "near_vertical_or_overhead_surface": finite_float(gravity.get("near_vertical_or_overhead_surface")),
        "floor_or_table_supported": finite_float(support.get("floor_or_table_supported")),
        "surface_type_matches_attachment": is_attachment_surface(surface_type, normal_class),
        "surface_normal_matches_attachment": is_attachment_normal(normal_class),
        "class_pair_prior_plausible": 1.0 if class_prior == "plausible" else 0.0,
        "predicate_label": evidence.get("predicate_label") or "unknown",
        "subtype_hint": evidence.get("subtype_hint") or "unknown",
        "surface_type": surface_type,
        "surface_normal_class": normal_class,
        "class_pair_prior": class_prior,
    }
    return values


def build_prepared_rows(
    strict_rows: list[dict[str, Any]],
    evidence_by_row_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    prepared: list[dict[str, Any]] = []
    errors: list[str] = []
    for row in strict_rows:
        evidence = evidence_by_row_id.get(row["row_id"])
        if evidence is None:
            errors.append(f"missing_evidence:{row['seed_id']}")
            continue
        label = int(row["calibration_label"])
        if label not in (0, 1):
            errors.append(f"non_binary_label:{row['seed_id']}")
            continue
        features = evidence_features(evidence)
        prepared.append(
            {
                **row,
                "_label": label,
                "_role": row["split_role"],
                "_features": features,
            }
        )
    return prepared, errors


def build_model_spec(train_rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_stats: dict[str, dict[str, float]] = {}
    for name in NUMERIC_FEATURES:
        values = [float(row["_features"][name]) for row in train_rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        numeric_stats[name] = {"mean": mean, "std": math.sqrt(variance) if variance > 0 else 1.0}
    categorical_values = {
        field: sorted({str(row["_features"][field]) for row in train_rows})
        for field in CATEGORICAL_FIELDS
    }
    feature_names = ["bias"] + [f"num:{name}" for name in NUMERIC_FEATURES]
    for field in CATEGORICAL_FIELDS:
        feature_names.extend(f"cat:{field}={value}" for value in categorical_values[field])
    return {
        "numeric_features": list(NUMERIC_FEATURES),
        "numeric_stats": numeric_stats,
        "categorical_fields": list(CATEGORICAL_FIELDS),
        "categorical_values": categorical_values,
        "feature_names": feature_names,
    }


def vectorize(row: dict[str, Any], spec: dict[str, Any]) -> list[float]:
    features = row["_features"]
    vector = [1.0]
    for name in spec["numeric_features"]:
        value = float(features[name])
        stats = spec["numeric_stats"][name]
        vector.append((value - stats["mean"]) / (stats["std"] or 1.0))
    for field in spec["categorical_fields"]:
        value = str(features[field])
        vector.extend(1.0 if value == item else 0.0 for item in spec["categorical_values"][field])
    return vector


def summarize_predictions(
    rows: list[dict[str, Any]],
    predictions: list[float],
    bins: int,
) -> dict[str, Any]:
    labels = [row["_label"] for row in rows]
    bin_rows, ece, mce = calibration_bins(predictions, labels, bins)
    by_label: dict[str, Any] = {}
    for predicate_label in sorted({row["predicate_label"] for row in rows}):
        indices = [index for index, row in enumerate(rows) if row["predicate_label"] == predicate_label]
        label_rows = [rows[index] for index in indices]
        label_predictions = [predictions[index] for index in indices]
        label_targets = [labels[index] for index in indices]
        by_label[predicate_label] = {
            "rows": len(label_rows),
            "positives": sum(label_targets),
            "negatives": len(label_targets) - sum(label_targets),
            "positive_rate": sum(label_targets) / len(label_targets) if label_targets else None,
            "mean_p_geom_valid": (
                sum(label_predictions) / len(label_predictions) if label_predictions else None
            ),
            "brier": brier_score(label_predictions, label_targets),
            "nll": log_loss(label_predictions, label_targets),
            "auroc_valid": auroc(label_predictions, label_targets),
            "auprc_valid": average_precision(label_predictions, label_targets),
        }
    return {
        "rows": len(rows),
        "positives": sum(labels),
        "negatives": len(labels) - sum(labels),
        "positive_rate": sum(labels) / len(labels) if labels else None,
        "mean_p_geom_valid": sum(predictions) / len(predictions) if predictions else None,
        "brier": brier_score(predictions, labels),
        "nll": log_loss(predictions, labels),
        "ece": ece,
        "mce": mce,
        "auroc_valid": auroc(predictions, labels),
        "auprc_valid": average_precision(predictions, labels),
        "invalid_detection": invalid_precision(predictions, labels),
        "calibration_bins": bin_rows,
        "by_predicate_label": by_label,
    }


def prior_predictions(rows: list[dict[str, Any]], prior: float) -> list[float]:
    return [prior] * len(rows)


def label_prior_predictions(
    rows: list[dict[str, Any]],
    label_prior: dict[str, float],
    fallback: float,
) -> list[float]:
    return [label_prior.get(row["predicate_label"], fallback) for row in rows]


def count_by_role(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for role in ("train", "dev"):
        scoped = [row for row in rows if row["_role"] == role]
        labels = [row["_label"] for row in scoped]
        result[role] = {
            "rows": len(scoped),
            "positives": sum(labels),
            "negatives": len(labels) - sum(labels),
            "by_predicate_label": dict(
                sorted(Counter(row["predicate_label"] for row in scoped).items())
            ),
            "by_subtype_hint": dict(sorted(Counter(row["subtype_hint"] for row in scoped).items())),
        }
    return result


def make_scores(rows: list[dict[str, Any]], probabilities: list[float], model_id: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row, probability in zip(rows, probabilities):
        output.append(
            {
                "schema_version": SCORE_SCHEMA_VERSION,
                "model_id": model_id,
                "seed_id": row["seed_id"],
                "row_id": row["row_id"],
                "case_id": row["case_id"],
                "role": row["_role"],
                "scan_id": row["scan_id"],
                "subgraph_id": row["subgraph_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "predicate_family": row["predicate_family"],
                "predicate_label": row["predicate_label"],
                "subtype_hint": row["subtype_hint"],
                "label": {
                    "geom_valid": row["_label"],
                    "source": "attachment_deferred_strict_filter",
                    "calibration_disposition": row["calibration_disposition"],
                },
                "p_geom_valid": probability,
                "p_geom_invalid": 1.0 - probability,
            }
        )
    return output


def report_md(manifest: dict[str, Any], metrics: dict[str, Any]) -> str:
    dev = metrics["conditions"]["logistic"]["dev"]
    train = metrics["conditions"]["logistic"]["train"]
    baseline = metrics["conditions"]["baselines"]["dev"]
    lines = [
        "# Attachment Deferred Calibration Fit",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        f"Model id: `{manifest['model_id']}`",
        "",
        "## Claim Boundary",
        "",
        "This fits a pooled attachment-deferred calibration model from the G4c",
        "strict-only filter. It does not score source predictions, compute source",
        "metrics, run controls/bootstrap, or change the current AAAI main claim.",
        "",
        "## Counts",
        "",
        f"- train rows: `{metrics['counts']['by_role']['train']['rows']}`",
        f"- dev rows: `{metrics['counts']['by_role']['dev']['rows']}`",
        f"- train positives/negatives: `{metrics['counts']['by_role']['train']['positives']}` / `{metrics['counts']['by_role']['train']['negatives']}`",
        f"- dev positives/negatives: `{metrics['counts']['by_role']['dev']['positives']}` / `{metrics['counts']['by_role']['dev']['negatives']}`",
        "",
        "## Dev Metrics",
        "",
        f"- Brier: `{dev['brier']}`",
        f"- NLL: `{dev['nll']}`",
        f"- ECE: `{dev['ece']}`",
        f"- AUROC(valid): `{dev['auroc_valid']}`",
        f"- AUPRC(valid): `{dev['auprc_valid']}`",
        "",
        "## Baselines",
        "",
        f"- constant_train_prior dev Brier/NLL/ECE: `{baseline['constant_train_prior']['brier']}` / `{baseline['constant_train_prior']['nll']}` / `{baseline['constant_train_prior']['ece']}`",
        f"- label_train_prior dev Brier/NLL/ECE: `{baseline['label_train_prior']['brier']}` / `{baseline['label_train_prior']['nll']}` / `{baseline['label_train_prior']['ece']}`",
        "",
        "## Train Metrics",
        "",
        f"- train Brier/NLL/ECE: `{train['brier']}` / `{train['nll']}` / `{train['ece']}`",
        "",
        "## Warnings",
        "",
    ]
    if metrics["warnings"]:
        lines.extend(f"- `{warning}`" for warning in metrics["warnings"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Use this fitted model to score attachment-deferred VL-SAT/Open3DSG source",
            "rows only after source evidence extraction is available. Then run source",
            "metrics and controls. Main AAAI claim promotion still requires explicit",
            "final user confirmation.",
            "",
        ]
    )
    return "\n".join(lines)


def commands_md() -> str:
    return """# Attachment Deferred G5 Calibration Fit Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \\
  attachment_deferred_calibration_fit
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/fit_attachment_strict_calibration.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/metrics.json >/dev/null
```

This command fits calibration only. It does not score source predictions,
compute source metrics, run controls/bootstrap, or update the main AAAI claim.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    strict_dir = args.strict_filter_dir if args.strict_filter_dir.is_absolute() else repo_root / args.strict_filter_dir
    gt_policy_dir = args.gt_policy_dir if args.gt_policy_dir.is_absolute() else repo_root / args.gt_policy_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out

    strict_manifest_path = strict_dir / "manifest.json"
    strict_rows_path = strict_dir / "strict_calibration_rows.jsonl"
    evidence_path = gt_policy_dir / "gt_evidence_rows.jsonl"
    for path in [strict_manifest_path, strict_rows_path, evidence_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing calibration input: {path}")

    strict_manifest = read_json(strict_manifest_path)
    if strict_manifest.get("status") != "attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics":
        raise ValueError(f"unexpected_strict_filter_status:{strict_manifest.get('status')}")

    strict_rows = list(iter_jsonl(strict_rows_path))
    evidence_by_row_id = {row["row_id"]: row for row in iter_jsonl(evidence_path)}
    prepared, errors = build_prepared_rows(strict_rows, evidence_by_row_id)
    if errors:
        raise ValueError(f"calibration_preparation_errors:{errors[:10]}")
    train_rows = [row for row in prepared if row["_role"] == "train"]
    dev_rows = [row for row in prepared if row["_role"] == "dev"]

    validation_errors: list[str] = []
    warnings: list[str] = []
    if not train_rows:
        validation_errors.append("zero_train_rows")
    if not dev_rows:
        validation_errors.append("zero_dev_rows")
    for role, rows in (("train", train_rows), ("dev", dev_rows)):
        labels = {row["_label"] for row in rows}
        if labels != {0, 1}:
            validation_errors.append(f"{role}_missing_binary_labels:{sorted(labels)}")
    if not any(row["predicate_label"] == "connected to" for row in dev_rows):
        warnings.append("connected_to_dev_absent_use_pooled_or_train_only_caveat")
    if validation_errors:
        raise ValueError(f"validation_errors:{validation_errors}")

    spec = build_model_spec(train_rows)
    train_vectors = [vectorize(row, spec) for row in train_rows]
    dev_vectors = [vectorize(row, spec) for row in dev_rows]
    train_labels = [row["_label"] for row in train_rows]
    dev_labels = [row["_label"] for row in dev_rows]
    weights, trace = fit_logistic(
        train_vectors,
        train_labels,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    train_prob = predict(train_vectors, weights)
    dev_prob = predict(dev_vectors, weights)
    dev_auroc = auroc(dev_prob, dev_labels)
    if dev_auroc is not None and dev_auroc >= 0.99:
        warnings.append("strict_subset_nearly_separable_not_source_metric_evidence")

    train_prior = sum(train_labels) / len(train_labels)
    label_prior: dict[str, float] = {}
    for predicate_label in sorted({row["predicate_label"] for row in train_rows}):
        scoped = [row for row in train_rows if row["predicate_label"] == predicate_label]
        label_prior[predicate_label] = sum(row["_label"] for row in scoped) / len(scoped)

    model_id = "h001-attachment-deferred-p-geom-valid-strict-v1"
    created_at = utc_now()
    metrics = {
        "schema_version": METRICS_SCHEMA_VERSION,
        "status": STATUS,
        "created_at": created_at,
        "model_id": model_id,
        "inputs": {
            "strict_filter_manifest": relpath(repo_root, strict_manifest_path),
            "strict_calibration_rows": relpath(repo_root, strict_rows_path),
            "gt_evidence_rows": relpath(repo_root, evidence_path),
        },
        "hyperparameters": {
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "bins": args.bins,
        },
        "counts": {
            "input_strict_rows": len(strict_rows),
            "used_rows": len(prepared),
            "by_role": count_by_role(prepared),
        },
        "conditions": {
            "logistic": {
                "train": summarize_predictions(train_rows, train_prob, args.bins),
                "dev": summarize_predictions(dev_rows, dev_prob, args.bins),
            },
            "baselines": {
                "dev": {
                    "constant_train_prior": summarize_predictions(
                        dev_rows,
                        prior_predictions(dev_rows, train_prior),
                        args.bins,
                    ),
                    "label_train_prior": summarize_predictions(
                        dev_rows,
                        label_prior_predictions(dev_rows, label_prior, train_prior),
                        args.bins,
                    ),
                },
            },
        },
        "training_trace": trace,
        "warnings": warnings,
        "notes": [
            "This is an attachment-deferred train/dev calibration fit from G4c strict rows.",
            "It uses point-contact, surface, OBB, gravity/support, predicate label, subtype, and coarse class-pair features.",
            "It does not use semantic source scores, source identity, seed strategy, or verifier status as model features.",
            "The strict filter excludes false-satisfied counterfactuals, false-violated positives, and uncertain rows.",
            "Near-perfect train/dev scores can occur because G4c keeps only strict policy-selected rows; source metrics are still required.",
            "No source prediction scoring or held-out source metrics are computed in this step.",
        ],
    }
    model = {
        "schema_version": MODEL_SCHEMA_VERSION,
        "status": STATUS,
        "created_at": created_at,
        "model_id": model_id,
        "source_split": "attachment_deferred_g4c_strict_filter",
        "feature_names": spec["feature_names"],
        "numeric_features": spec["numeric_features"],
        "numeric_stats": spec["numeric_stats"],
        "categorical_fields": spec["categorical_fields"],
        "categorical_values": spec["categorical_values"],
        "weights": weights,
        "hyperparameters": metrics["hyperparameters"],
        "train_prior": train_prior,
        "label_prior": label_prior,
        "notes": metrics["notes"],
    }
    scores = make_scores(train_rows, train_prob, model_id) + make_scores(dev_rows, dev_prob, model_id)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": created_at,
        "model_id": model_id,
        "claim_boundary": {
            "artifact_type": "attachment_deferred_calibration_fit",
            "calibration_fitted": True,
            "source_predictions_scored": False,
            "source_metrics_computed": False,
            "controls_run": False,
            "bootstrap_ci_run": False,
            "current_main_claim_unchanged": True,
            "requires_user_confirmation_before_main_claim_promotion": True,
        },
        "inputs": metrics["inputs"],
        "outputs": {
            "manifest": "manifest.json",
            "model": "model.json",
            "metrics": "metrics.json",
            "scores": "scores.jsonl",
            "commands": "commands.md",
            "report": "report.md",
        },
        "counts": metrics["counts"],
        "dev_metrics": metrics["conditions"]["logistic"]["dev"],
        "warnings": warnings,
        "blockers": [
            "source_predictions_not_scored",
            "source_metrics_not_run",
            "controls_not_run",
            "bootstrap_ci_not_run",
            "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
        ],
        "next_gate": "G5_attachment_source_scoring_and_metrics",
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "model.json", model)
    write_json(out / "metrics.json", metrics)
    write_jsonl(out / "scores.jsonl", scores)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, metrics))
    print(
        json.dumps(
            {
                "status": STATUS,
                "out": relpath(repo_root, out),
                "train_rows": len(train_rows),
                "dev_rows": len(dev_rows),
                "dev_brier": metrics["conditions"]["logistic"]["dev"]["brier"],
                "dev_nll": metrics["conditions"]["logistic"]["dev"]["nll"],
                "dev_auroc": metrics["conditions"]["logistic"]["dev"]["auroc_valid"],
                "warnings": warnings,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
