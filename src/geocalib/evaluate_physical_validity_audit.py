#!/usr/bin/env python3
"""Validate H001 audit labels and estimate human validity/calibration metrics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "h001_physical_validity_audit_evaluation_v1"
ALLOWED_LABELS = {"physically_valid", "physically_invalid", "ambiguous", "unobservable"}
FORBIDDEN_HUMAN_REVIEWER_TOKENS = {
    "codex", "openai", "chatgpt", "gpt", "llm", "ai_proxy", "proxy_agent",
}
CONDITIONS = {
    "semantic_only": "semantic_only",
    "family_conditional_risk": "family_conditional_risk",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/frozen_v1"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/evaluation_v1"),
    )
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260710)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def labels_by_id(rows: list[dict[str, str]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for row in rows:
        label = row.get("physical_validity_label", "").strip()
        if label:
            output[row["audit_id"]] = label
    return output


def adjudication_by_id(rows: list[dict[str, str]]) -> dict[str, str]:
    return {
        row["audit_id"]: row.get("adjudicated_label", "").strip()
        for row in rows
        if row.get("adjudicated_label", "").strip()
    }


def reviewer_provenance(
    rows: list[dict[str, str]],
    *,
    label_field: str,
    reviewer_field: str,
    timestamp_field: str,
) -> dict[str, Any]:
    labeled = [row for row in rows if row.get(label_field, "").strip()]
    reviewer_ids = sorted({row.get(reviewer_field, "").strip() for row in labeled if row.get(reviewer_field, "").strip()})
    missing_reviewer = [row.get("audit_id", "") for row in labeled if not row.get(reviewer_field, "").strip()]
    missing_timestamp = [row.get("audit_id", "") for row in labeled if not row.get(timestamp_field, "").strip()]
    forbidden = sorted(
        reviewer_id
        for reviewer_id in reviewer_ids
        if any(token in reviewer_id.casefold() for token in FORBIDDEN_HUMAN_REVIEWER_TOKENS)
    )
    return {
        "labeled_rows": len(labeled),
        "reviewer_ids": reviewer_ids,
        "missing_reviewer_rows": len(missing_reviewer),
        "missing_timestamp_rows": len(missing_timestamp),
        "forbidden_proxy_reviewer_ids": forbidden,
    }


def cohen_kappa(a: dict[str, str], b: dict[str, str]) -> dict[str, Any]:
    common = sorted(set(a) & set(b))
    if not common:
        return {"n": 0, "observed_agreement": None, "cohen_kappa": None}
    labels = sorted(ALLOWED_LABELS)
    observed = sum(a[key] == b[key] for key in common) / len(common)
    counts_a = Counter(a[key] for key in common)
    counts_b = Counter(b[key] for key in common)
    expected = sum((counts_a[label] / len(common)) * (counts_b[label] / len(common)) for label in labels)
    kappa = (observed - expected) / (1.0 - expected) if expected < 1.0 else 1.0
    return {"n": len(common), "observed_agreement": observed, "cohen_kappa": kappa}


def percentile(values: np.ndarray) -> list[float | None]:
    finite = values[np.isfinite(values)]
    if not len(finite):
        return [None, None]
    low, high = np.percentile(finite, [2.5, 97.5])
    return [float(low), float(high)]


def weighted_ratio(rows: list[dict[str, Any]]) -> float | None:
    denominator = sum(row["weight"] for row in rows)
    if denominator <= 0:
        return None
    return sum(row["weight"] * row["invalid"] for row in rows) / denominator


def bootstrap_ratio(rows: list[dict[str, Any]], n: int, seed: int) -> list[float | None]:
    if not rows:
        return [None, None]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["scan_id"]].append(row)
    scans = sorted(grouped)
    rng = np.random.default_rng(seed)
    samples = np.full(n, np.nan, dtype=np.float64)
    for index in range(n):
        chosen = rng.choice(scans, size=len(scans), replace=True)
        sample_rows = [row for scan in chosen for row in grouped[str(scan)]]
        value = weighted_ratio(sample_rows)
        if value is not None:
            samples[index] = value
    return percentile(samples)


def weighted_brier(rows: list[dict[str, Any]], score_field: str) -> float | None:
    denominator = sum(row["weight"] for row in rows)
    if denominator <= 0:
        return None
    return sum(row["weight"] * (row[score_field] - row["valid"]) ** 2 for row in rows) / denominator


def weighted_auc(rows: list[dict[str, Any]], score_field: str) -> float | None:
    positives = [row for row in rows if row["valid"] == 1]
    negatives = [row for row in rows if row["valid"] == 0]
    denominator = sum(row["weight"] for row in positives) * sum(row["weight"] for row in negatives)
    if denominator <= 0:
        return None
    numerator = 0.0
    for positive in positives:
        for negative in negatives:
            comparison = 1.0 if positive[score_field] > negative[score_field] else (0.5 if positive[score_field] == negative[score_field] else 0.0)
            numerator += positive["weight"] * negative["weight"] * comparison
    return numerator / denominator


def weighted_auprc(rows: list[dict[str, Any]], score_field: str) -> float | None:
    total_positive = sum(row["weight"] for row in rows if row["valid"] == 1)
    if total_positive <= 0:
        return None
    ordered = sorted(rows, key=lambda row: (-row[score_field], row["audit_id"]))
    tp = 0.0
    fp = 0.0
    previous_recall = 0.0
    area = 0.0
    for row in ordered:
        if row["valid"]:
            tp += row["weight"]
        else:
            fp += row["weight"]
        recall = tp / total_positive
        precision = tp / (tp + fp)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area


def weighted_ece(rows: list[dict[str, Any]], score_field: str, bins: int = 10) -> dict[str, Any]:
    if not rows:
        return {"ece_equal_width": None, "bins": []}
    total = sum(row["weight"] for row in rows)
    details = []
    ece = 0.0
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        selected = [
            row for row in rows
            if row[score_field] >= lower and (row[score_field] < upper or (index == bins - 1 and row[score_field] <= upper))
        ]
        weight = sum(row["weight"] for row in selected)
        if weight:
            confidence = sum(row["weight"] * row[score_field] for row in selected) / weight
            accuracy = sum(row["weight"] * row["valid"] for row in selected) / weight
            ece += (weight / total) * abs(confidence - accuracy)
        else:
            confidence = None
            accuracy = None
        details.append({"lower": lower, "upper": upper, "rows": len(selected), "weight": weight, "mean_score": confidence, "valid_rate": accuracy})
    return {"ece_equal_width": ece, "bins": details}


def logit(value: float) -> float:
    clipped = min(max(value, 1e-6), 1.0 - 1e-6)
    return math.log(clipped / (1.0 - clipped))


def sigmoid(value: np.ndarray) -> np.ndarray:
    return np.where(
        value >= 0,
        1.0 / (1.0 + np.exp(-value)),
        np.exp(value) / (1.0 + np.exp(value)),
    )


def fit_platt(rows: list[dict[str, Any]]) -> dict[str, Any]:
    x_raw = np.asarray([logit(row["semantic_score"]) for row in rows], dtype=np.float64)
    y = np.asarray([row["valid"] for row in rows], dtype=np.float64)
    weights = np.asarray([row["weight"] for row in rows], dtype=np.float64)
    mean = float(np.average(x_raw, weights=weights))
    variance = float(np.average((x_raw - mean) ** 2, weights=weights))
    scale = max(math.sqrt(variance), 1e-6)
    x = (x_raw - mean) / scale
    parameters = np.asarray([0.0, 1.0], dtype=np.float64)
    total_weight = max(float(weights.sum()), 1e-12)
    for _ in range(1500):
        probabilities = sigmoid(parameters[0] + parameters[1] * x)
        residual = probabilities - y
        gradient = np.asarray(
            [
                float(np.sum(weights * residual) / total_weight),
                float(np.sum(weights * residual * x) / total_weight + 1e-4 * parameters[1]),
            ]
        )
        parameters -= 0.05 * gradient
        parameters[1] = max(parameters[1], 0.0)
    return {
        "intercept": float(parameters[0]),
        "slope_standardized_logit": float(parameters[1]),
        "logit_mean": mean,
        "logit_scale": scale,
        "train_rows": len(rows),
        "train_valid": int(y.sum()),
        "train_invalid": int(len(y) - y.sum()),
    }


def apply_platt(score: float, model: dict[str, Any]) -> float:
    standardized = (logit(score) - model["logit_mean"]) / model["logit_scale"]
    value = model["intercept"] + model["slope_standardized_logit"] * standardized
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def crossfit_platt(rows: list[dict[str, Any]], seed: int, folds: int = 5) -> list[dict[str, Any]]:
    fold_by_scan = {
        scan_id: int(hashlib.sha256(f"{seed}|{scan_id}".encode("utf-8")).hexdigest(), 16) % folds
        for scan_id in {row["scan_id"] for row in rows}
    }
    models: list[dict[str, Any]] = []
    for fold in range(folds):
        train = [row for row in rows if fold_by_scan[row["scan_id"]] != fold]
        test = [row for row in rows if fold_by_scan[row["scan_id"]] == fold]
        if not test:
            models.append({"fold": fold, "status": "empty_test_fold", "test_rows": 0})
            continue
        if len({row["valid"] for row in train}) < 2:
            for row in test:
                row["semantic_platt_crossfit"] = row["semantic_score"]
            models.append({"fold": fold, "status": "insufficient_train_classes", "test_rows": len(test)})
            continue
        model = fit_platt(train)
        for row in test:
            row["semantic_platt_crossfit"] = apply_platt(row["semantic_score"], model)
        models.append({"fold": fold, "status": "fit", "test_rows": len(test), **model})
    missing = [row["audit_id"] for row in rows if "semantic_platt_crossfit" not in row]
    if missing:
        raise RuntimeError(f"missing_crossfit_scores:{len(missing)}")
    return models


def calibration_summary(rows: list[dict[str, Any]], score_field: str) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "weighted_valid_prevalence": (
            sum(row["weight"] * row["valid"] for row in rows) / sum(row["weight"] for row in rows)
            if rows and sum(row["weight"] for row in rows) > 0 else None
        ),
        "weighted_brier": weighted_brier(rows, score_field),
        "weighted_auroc": weighted_auc(rows, score_field),
        "weighted_auprc": weighted_auprc(rows, score_field),
        **weighted_ece(rows, score_field),
    }


def make_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Independent Physical-Validity Audit Evaluation",
        "",
        f"Status: `{summary['status']}`",
        f"Created at UTC: `{summary['created_at_utc']}`",
        "",
    ]
    if summary["status"] == "awaiting_independent_human_labels":
        lines.extend(
            [
                "The audit runner and estimands are frozen, but no independent human labels are present.",
                "No human Violation@K or semantic-calibration number has been fabricated.",
                "",
                f"- Annotator A labeled: `{summary['label_counts']['annotator_a']}` / `{summary['label_counts']['expected']}`",
                f"- Annotator B labeled: `{summary['label_counts']['annotator_b']}` / `{summary['label_counts']['expected']}`",
                f"- Adjudicated: `{summary['label_counts']['adjudicated']}`",
                "",
            ]
        )
        return "\n".join(lines)
    if summary["status"] != "ready":
        lines.extend(
            [
                "Human evidence is not reportable because the frozen independence/provenance gate did not pass.",
                "Codex, LLM, and proxy reviewer identifiers cannot be counted as human annotators.",
                "See `summary.json` for the exact blocking provenance fields.",
                "",
            ]
        )
        return "\n".join(lines)
    lines.extend(
        [
            "## Agreement",
            "",
            f"- Common first-pass rows: `{summary['agreement']['n']}`",
            f"- Observed agreement: `{summary['agreement']['observed_agreement']}`",
            f"- Cohen kappa: `{summary['agreement']['cohen_kappa']}`",
            "",
            "## Human Violation@K",
            "",
            "See `summary.json` for source/context/family/K design-weighted estimates and cluster-bootstrap CIs.",
            "",
            "## Semantic calibration",
            "",
            "See `summary.json` for design-weighted Brier, AUROC, AUPRC, ECE, and reliability bins.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    audit_dir = resolve(root, args.audit_dir)
    out = resolve(root, args.out)
    manifest = json.loads((audit_dir / "manifest.json").read_text(encoding="utf-8"))
    sidecar = read_jsonl(audit_dir / "private_sidecar.jsonl")
    rows_a = read_csv(audit_dir / "annotator_a.csv")
    rows_b = read_csv(audit_dir / "annotator_b.csv")
    adjudication_rows = read_csv(audit_dir / "adjudication.csv")
    expected_ids = {row["audit_id"] for row in sidecar}
    sheet_a_ids = [row.get("audit_id", "") for row in rows_a]
    sheet_b_ids = [row.get("audit_id", "") for row in rows_b]
    if len(sheet_a_ids) != len(set(sheet_a_ids)) or set(sheet_a_ids) != expected_ids:
        raise ValueError("annotator_a_id_contract_failed")
    if len(sheet_b_ids) != len(set(sheet_b_ids)) or set(sheet_b_ids) != expected_ids:
        raise ValueError("annotator_b_id_contract_failed")
    if {row.get("audit_id", "") for row in adjudication_rows} != expected_ids:
        raise ValueError("adjudication_id_contract_failed")
    labels_a = labels_by_id(rows_a)
    labels_b = labels_by_id(rows_b)
    adjudicated = adjudication_by_id(adjudication_rows)
    invalid_values = sorted((set(labels_a.values()) | set(labels_b.values()) | set(adjudicated.values())) - ALLOWED_LABELS)
    if invalid_values:
        raise ValueError(f"invalid_labels:{invalid_values}")

    provenance_a = reviewer_provenance(
        rows_a,
        label_field="physical_validity_label",
        reviewer_field="reviewer_id",
        timestamp_field="reviewed_at",
    )
    provenance_b = reviewer_provenance(
        rows_b,
        label_field="physical_validity_label",
        reviewer_field="reviewer_id",
        timestamp_field="reviewed_at",
    )
    provenance_adjudicator = reviewer_provenance(
        adjudication_rows,
        label_field="adjudicated_label",
        reviewer_field="adjudicator_id",
        timestamp_field="adjudicated_at",
    )

    expected = len(sidecar)
    status = "ready"
    if len(labels_a) < expected or len(labels_b) < expected:
        status = "awaiting_independent_human_labels"

    first_pass_provenance_valid = (
        len(provenance_a["reviewer_ids"]) == 1
        and len(provenance_b["reviewer_ids"]) == 1
        and provenance_a["reviewer_ids"] != provenance_b["reviewer_ids"]
        and provenance_a["missing_reviewer_rows"] == 0
        and provenance_b["missing_reviewer_rows"] == 0
        and provenance_a["missing_timestamp_rows"] == 0
        and provenance_b["missing_timestamp_rows"] == 0
        and not provenance_a["forbidden_proxy_reviewer_ids"]
        and not provenance_b["forbidden_proxy_reviewer_ids"]
    )
    if status == "ready" and not first_pass_provenance_valid:
        status = "blocked_invalid_or_nonindependent_human_provenance"

    primary_labels: dict[str, str] = {}
    unresolved: list[str] = []
    if status == "ready":
        for audit_id in sorted(set(labels_a) | set(labels_b)):
            if labels_a.get(audit_id) == labels_b.get(audit_id):
                primary_labels[audit_id] = labels_a[audit_id]
            elif audit_id in adjudicated:
                primary_labels[audit_id] = adjudicated[audit_id]
            else:
                unresolved.append(audit_id)
        if unresolved:
            status = "awaiting_blinded_adjudication"

    adjudication_provenance_valid = True
    if adjudicated:
        first_pass_ids = set(provenance_a["reviewer_ids"] + provenance_b["reviewer_ids"])
        adjudication_provenance_valid = (
            len(provenance_adjudicator["reviewer_ids"]) == 1
            and not (set(provenance_adjudicator["reviewer_ids"]) & first_pass_ids)
            and provenance_adjudicator["missing_reviewer_rows"] == 0
            and provenance_adjudicator["missing_timestamp_rows"] == 0
            and not provenance_adjudicator["forbidden_proxy_reviewer_ids"]
        )
        if status == "ready" and not adjudication_provenance_valid:
            status = "blocked_invalid_or_nonblinded_adjudication_provenance"

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "audit_manifest_status": manifest.get("status"),
        "audit_dir": relpath(root, audit_dir),
        "label_counts": {
            "expected": expected,
            "annotator_a": len(labels_a),
            "annotator_b": len(labels_b),
            "adjudicated": len(adjudicated),
            "unresolved_disagreements": len(unresolved),
        },
        "agreement": cohen_kappa(labels_a, labels_b),
        "human_reviewer_provenance": {
            "annotator_a": provenance_a,
            "annotator_b": provenance_b,
            "adjudicator": provenance_adjudicator,
            "first_pass_distinct_nonproxy_reviewers": first_pass_provenance_valid,
            "adjudicator_distinct_nonproxy_if_used": adjudication_provenance_valid,
            "policy": "two complete first-pass sheets require distinct non-proxy reviewer IDs and timestamps; adjudication requires a third distinct non-proxy reviewer when used",
        },
        "human_violation_at_k": {},
        "semantic_calibration": {},
        "label_policy": "valid/invalid binary denominator; ambiguous and unobservable reported as coverage exclusions",
        "n_bootstrap": args.n_bootstrap,
        "seed": args.seed,
    }

    if status == "ready":
        analysis_rows: list[dict[str, Any]] = []
        coverage = Counter()
        for item in sidecar:
            label = primary_labels[item["audit_id"]]
            coverage[label] += 1
            if label not in {"physically_valid", "physically_invalid"}:
                continue
            for record in item["source_records"]:
                analysis_rows.append(
                    {
                        "audit_id": item["audit_id"],
                        "scan_id": record["scan_id"],
                        "source": record["source"],
                        "family": record["predicate_family"],
                        "weight": float(item["design_weight"]),
                        "valid": int(label == "physically_valid"),
                        "invalid": int(label == "physically_invalid"),
                        "semantic_score": float(record["semantic_score"]),
                        "family_conditional_risk": float(record["family_conditional_risk"]),
                        "ranks": record["ranks"],
                    }
                )
        summary["label_coverage"] = dict(sorted(coverage.items()))
        for source in sorted({row["source"] for row in analysis_rows}):
            source_rows = [row for row in analysis_rows if row["source"] == source]
            platt_models = crossfit_platt(source_rows, args.seed)
            summary["semantic_calibration"][source] = {
                "raw_semantic_overall": calibration_summary(source_rows, "semantic_score"),
                "crossfitted_platt_overall": calibration_summary(
                    source_rows, "semantic_platt_crossfit"
                ),
                "raw_semantic_by_family": {
                    family: calibration_summary(
                        [row for row in source_rows if row["family"] == family], "semantic_score"
                    )
                    for family in sorted({row["family"] for row in source_rows})
                },
                "crossfitted_platt_by_family": {
                    family: calibration_summary(
                        [row for row in source_rows if row["family"] == family],
                        "semantic_platt_crossfit",
                    )
                    for family in sorted({row["family"] for row in source_rows})
                },
                "crossfit_protocol": {
                    "folds": 5,
                    "group": "scan_id",
                    "fit": "weighted monotone Platt scaling on logit semantic score",
                    "models": platt_models,
                },
            }
            summary["human_violation_at_k"][source] = {}
            for context in ("global_in_scope", "within_family"):
                summary["human_violation_at_k"][source][context] = {}
                family_scopes: list[str | None] = [None] + sorted({row["family"] for row in source_rows})
                for family in family_scopes:
                    family_key = family or "all_families"
                    summary["human_violation_at_k"][source][context][family_key] = {}
                    scoped = source_rows if family is None else [row for row in source_rows if row["family"] == family]
                    for condition in CONDITIONS:
                        by_k = {}
                        for k in manifest["scope"]["ks"]:
                            selected = [
                                row for row in scoped
                                if int(row["ranks"][f"{context}:{condition}"]) <= int(k)
                            ]
                            point = weighted_ratio(selected)
                            by_k[str(k)] = {
                                "point": point,
                                "ci95_cluster_bootstrap": bootstrap_ratio(
                                    selected, args.n_bootstrap, args.seed + int(k)
                                ),
                                "audited_binary_rows": len(selected),
                                "design_weight_sum": sum(row["weight"] for row in selected),
                            }
                        summary["human_violation_at_k"][source][context][family_key][condition] = by_k

    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "summary.json", summary)
    (out / "summary.md").write_text(make_report(summary), encoding="utf-8")
    write_json(
        out / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": summary["created_at_utc"],
            "status": summary["status"],
            "inputs": {
                "audit_manifest": relpath(root, audit_dir / "manifest.json"),
                "annotator_a": relpath(root, audit_dir / "annotator_a.csv"),
                "annotator_b": relpath(root, audit_dir / "annotator_b.csv"),
                "adjudication": relpath(root, audit_dir / "adjudication.csv"),
            },
            "outputs": [relpath(root, out / "summary.json"), relpath(root, out / "summary.md")],
            "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_audit_evaluate",
        },
    )
    print(json.dumps({"status": status, "out": relpath(root, out), "expected": expected}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
