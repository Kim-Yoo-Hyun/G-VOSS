#!/usr/bin/env python3
"""Fit and evaluate the attachment subtype-v2 development diagnostic.

The design is retrospective and remains outside the paper claim.  It uses only
the candidate strict rows frozen by ``redesign_attachment_subtypes.py`` and
applies a neutral compatibility factor to abstained/positive-only routes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from fit_attachment_strict_calibration import (
    evidence_features,
    fit_logistic,
    predict,
    summarize_predictions,
)
from redesign_attachment_subtypes import route_evidence
from run_attachment_full_source_g5d import (
    condition_scores,
    exact_key_from_parts,
    gt_key,
    select_topk_by_subgraph,
    source_metrics,
)
from run_attachment_gt_policy_smoke import decision_row, policy_thresholds
from run_attachment_source_scoring_preflight import row_id_for_source


SCHEMA_VERSION = "h001_attachment_subtype_v2_development_diagnostic_v1"
STATUS = "attachment_subtype_v2_development_diagnostic_ready"
PREDICATES = ("attached to", "hanging on")
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
)
CATEGORICAL_FIELDS = ("mechanism", "surface_type", "surface_normal_class")
CONDITION_RENAME = {
    "semantic_only": "source_score",
    "probabilistic_recalibrated": "selective_family_product",
    "rule_verified_attachment_policy": "legacy_hard_filter",
    "control_p_geom_valid_only": "effective_compatibility_only",
    "control_distance_only": "distance_only",
    "control_shuffled_geometry": "shuffled_compatibility",
    "control_wrong_pair_geometry": "wrong_pair_compatibility",
}


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid_jsonl:{path}:{line_number}:{exc}") from exc


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return default


def prepared_features(evidence: dict[str, Any], mechanism: str) -> dict[str, Any]:
    legacy = evidence_features(evidence)
    return {
        **{name: finite(legacy.get(name)) for name in NUMERIC_FEATURES},
        "mechanism": mechanism,
        "surface_type": str(legacy.get("surface_type", "unknown")),
        "surface_normal_class": str(
            legacy.get("surface_normal_class", "unknown")
        ),
    }


def build_spec(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stats: dict[str, dict[str, float]] = {}
    for name in NUMERIC_FEATURES:
        values = [float(row["features"][name]) for row in rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        stats[name] = {
            "mean": mean,
            "std": math.sqrt(variance) if variance > 0 else 1.0,
        }
    categories = {
        field: sorted({str(row["features"][field]) for row in rows})
        for field in CATEGORICAL_FIELDS
    }
    names = ["bias"] + [f"num:{name}" for name in NUMERIC_FEATURES]
    for field in CATEGORICAL_FIELDS:
        names.extend(f"cat:{field}={value}" for value in categories[field])
    return {
        "numeric_features": list(NUMERIC_FEATURES),
        "numeric_stats": stats,
        "categorical_fields": list(CATEGORICAL_FIELDS),
        "categorical_values": categories,
        "feature_names": names,
    }


def vectorize(features: dict[str, Any], spec: dict[str, Any]) -> list[float]:
    vector = [1.0]
    for name in spec["numeric_features"]:
        stats = spec["numeric_stats"][name]
        vector.append((float(features[name]) - stats["mean"]) / stats["std"])
    for field in spec["categorical_fields"]:
        value = str(features[field])
        vector.extend(
            1.0 if value == category else 0.0
            for category in spec["categorical_values"][field]
        )
    return vector


def load_training_rows(root: Path, redesign: Path) -> list[dict[str, Any]]:
    evidence = {
        str(row["row_id"]): row
        for row in iter_jsonl(root / "gt_policy_smoke/gt_evidence_rows.jsonl")
    }
    rows: list[dict[str, Any]] = []
    for migration in iter_jsonl(redesign / "migration_rows.jsonl"):
        if migration["migration_disposition"] != "candidate_strict_calibration":
            continue
        predicate = str(migration["predicate_label"])
        if predicate not in PREDICATES:
            continue
        row_evidence = evidence.get(str(migration["row_id"]))
        if row_evidence is None:
            raise ValueError(f"missing_training_evidence:{migration['row_id']}")
        rows.append(
            {
                "row_id": migration["row_id"],
                "split_role": migration["split_role"],
                "predicate_label": predicate,
                "mechanism": migration["mechanism"],
                "label": int(migration["target_geom_valid"]),
                "features": prepared_features(
                    row_evidence, str(migration["mechanism"])
                ),
            }
        )
    return rows


def fit_models(
    rows: list[dict[str, Any]], *, epochs: int, learning_rate: float, l2: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    models: dict[str, Any] = {}
    diagnostics: dict[str, Any] = {}
    for predicate in PREDICATES:
        train = [
            row
            for row in rows
            if row["predicate_label"] == predicate and row["split_role"] == "train"
        ]
        dev = [
            row
            for row in rows
            if row["predicate_label"] == predicate and row["split_role"] == "dev"
        ]
        for role, scoped in (("train", train), ("dev", dev)):
            labels = [row["label"] for row in scoped]
            if not scoped or len(set(labels)) != 2:
                raise ValueError(
                    f"nonbinary_or_empty_{role}:{predicate}:{len(scoped)}:{sorted(set(labels))}"
                )
        spec = build_spec(train)
        train_vectors = [vectorize(row["features"], spec) for row in train]
        dev_vectors = [vectorize(row["features"], spec) for row in dev]
        weights, trace = fit_logistic(
            train_vectors,
            [row["label"] for row in train],
            epochs=epochs,
            learning_rate=learning_rate,
            l2=l2,
        )
        train_pred = predict(train_vectors, weights)
        dev_pred = predict(dev_vectors, weights)
        models[predicate] = {
            "predicate_label": predicate,
            "spec": spec,
            "weights": weights,
            "training_trace": trace,
        }
        metrics_train_rows = [
            {"_label": row["label"], "predicate_label": predicate} for row in train
        ]
        metrics_dev_rows = [
            {"_label": row["label"], "predicate_label": predicate} for row in dev
        ]
        diagnostics[predicate] = {
            "counts": {
                "train": len(train),
                "train_positive": sum(row["label"] for row in train),
                "train_negative": len(train) - sum(row["label"] for row in train),
                "dev": len(dev),
                "dev_positive": sum(row["label"] for row in dev),
                "dev_negative": len(dev) - sum(row["label"] for row in dev),
            },
            "train": summarize_predictions(metrics_train_rows, train_pred, 10),
            "dev": summarize_predictions(metrics_dev_rows, dev_pred, 10),
        }
    model = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "model_id": "attachment-subtype-v2-selective-product-development-v1",
        "fit_scope": "candidate_strict_calibration_only",
        "models": models,
        "neutral_fallback": 1.0,
        "forbidden_inputs": [
            "source_score",
            "source_rank",
            "source_id",
            "class_pair_prior",
            "legacy_subtype_hint",
        ],
        "hyperparameters": {
            "epochs": epochs,
            "learning_rate": learning_rate,
            "l2": l2,
        },
    }
    return model, diagnostics


def score_compatibility(
    evidence: dict[str, Any], route: dict[str, str], model: dict[str, Any]
) -> tuple[float, str]:
    if route["applicability"] != "bidirectional_compatibility":
        return 1.0, "neutral_fallback"
    predicate = str(evidence["predicate_label"])
    predicate_model = model["models"].get(predicate)
    if predicate_model is None:
        return 1.0, "neutral_missing_model"
    features = prepared_features(evidence, route["mechanism"])
    vector = vectorize(features, predicate_model["spec"])
    probability = predict([vector], predicate_model["weights"])[0]
    return float(probability), "fitted_bidirectional_compatibility"


def effective_multiplier(
    compatibility: float, route: dict[str, str], fusion: str
) -> float:
    if route["applicability"] != "bidirectional_compatibility":
        return 1.0
    if fusion == "bounded_symmetric":
        return 0.5 + compatibility
    if fusion == "raw_selective":
        return compatibility
    raise ValueError(f"unknown_fusion:{fusion}")


def load_scored_source_rows(
    root: Path, model: dict[str, Any], fusion: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    thresholds = policy_thresholds(
        read_json(root / "verifier_policy/verifier_policy.json")
    )
    output: list[dict[str, Any]] = []
    counts: dict[str, Any] = {
        "rows": 0,
        "by_source": Counter(),
        "by_applicability": Counter(),
        "by_score_origin": Counter(),
    }
    for shard_dir in sorted((root / "full_validation_g5d/shards").iterdir()):
        if not shard_dir.is_dir():
            continue
        source_path = shard_dir / "source_rows.jsonl"
        evidence_path = shard_dir / "evidence_rows.jsonl"
        if not source_path.exists() or not evidence_path.exists():
            continue
        source_iter = iter_jsonl(source_path)
        evidence_iter = iter_jsonl(evidence_path)
        local_count = 0
        while True:
            try:
                source = next(source_iter)
            except StopIteration:
                source = None
            try:
                evidence = next(evidence_iter)
            except StopIteration:
                evidence = None
            if source is None and evidence is None:
                break
            if source is None or evidence is None:
                raise ValueError(f"shard_row_count_mismatch:{shard_dir}")
            expected_row_id = row_id_for_source(source)
            if str(evidence.get("row_id")) != expected_row_id:
                raise ValueError(
                    f"shard_identity_mismatch:{shard_dir}:{evidence.get('row_id')}!={expected_row_id}"
                )
            route = route_evidence(evidence)
            compatibility, score_origin = score_compatibility(evidence, route, model)
            multiplier = effective_multiplier(compatibility, route, fusion)
            decision = decision_row(evidence, thresholds)
            semantic_score = finite(
                source.get("ranking_score", source.get("semantic_score", 0.0))
            )
            point = evidence.get("point_contact_evidence", {})
            available = evidence.get("geometry_available", {})
            output.append(
                {
                    "source_name": source["source_name"],
                    "source_prediction_id": source["source_prediction_id"],
                    "scan_id": source["scan_id"],
                    "subgraph_id": source["subgraph_id"],
                    "subject_id": int(source["subject_id"]),
                    "object_id": int(source["object_id"]),
                    "predicate_label": source["predicate_label"],
                    "semantic": {
                        "ranking_score": semantic_score,
                        "predicate_score": finite(source.get("semantic_score")),
                    },
                    # ``source_metrics`` treats this field as the multiplicative
                    # condition score. The raw probability is retained separately.
                    "p_geom_valid": multiplier,
                    "v2_compatibility_probability": compatibility,
                    "v2_effective_multiplier": multiplier,
                    "attachment_policy_decision": decision["verification_status"],
                    "feature_snapshot": {
                        "min_point_distance_m": point.get("min_point_distance_m")
                    },
                    "evidence": {"geometry_available": available},
                    "v2_route": route,
                    "v2_score_origin": score_origin,
                }
            )
            local_count += 1
            counts["rows"] += 1
            counts["by_source"][str(source["source_name"])] += 1
            counts["by_applicability"][route["applicability"]] += 1
            counts["by_score_origin"][score_origin] += 1
        status = read_json(shard_dir / "status.json")
        expected = int(status["counts"]["evidence_rows"])
        if local_count != expected:
            raise ValueError(
                f"shard_expected_count_mismatch:{shard_dir}:{local_count}!={expected}"
            )
    return output, {
        "rows": counts["rows"],
        "by_source": dict(sorted(counts["by_source"].items())),
        "by_applicability": dict(sorted(counts["by_applicability"].items())),
        "by_score_origin": dict(sorted(counts["by_score_origin"].items())),
    }


def condition_names(fusion: str) -> dict[str, str]:
    names = dict(CONDITION_RENAME)
    if fusion == "bounded_symmetric":
        names["probabilistic_recalibrated"] = "selective_bounded_product"
        names["control_p_geom_valid_only"] = "effective_multiplier_only"
    return names


def rename_conditions(
    payload: dict[str, Any], *, fusion: str, bootstrap: bool = False
) -> None:
    names = condition_names(fusion)
    if bootstrap:
        for source in payload["sources"].values():
            source["conditions"] = {
                names[name]: value
                for name, value in source["conditions"].items()
            }
    else:
        for source in payload["conditions"].values():
            source["conditions"] = {
                names[name]: value
                for name, value in source["conditions"].items()
            }


def percentile_ci(values: np.ndarray) -> list[float | None]:
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return [None, None]
    lo, hi = np.percentile(finite_values, [2.5, 97.5])
    return [float(lo), float(hi)]


def paired_delta_bootstrap(
    rows: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    *,
    ks: list[int],
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    gt_all = [
        row
        for row in ground_truth
        if row.get("predicate_label")
        in {"attached to", "hanging on", "connected to"}
    ]
    output: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "sources": {},
    }
    for source_name in sorted({str(row["source_name"]) for row in rows}):
        source_rows = [row for row in rows if row["source_name"] == source_name]
        exact_keys = {exact_key_from_parts(row) for row in source_rows}
        covered_gt = [row for row in gt_all if gt_key(row) in exact_keys]
        gt_by_subgraph: dict[str, set[tuple[str, str, int, int, str]]] = {}
        for gt_row in covered_gt:
            gt_by_subgraph.setdefault(str(gt_row["subgraph_id"]), set()).add(
                gt_key(gt_row)
            )
        subgraphs = sorted(
            set(gt_by_subgraph)
            | {str(row["subgraph_id"]) for row in source_rows}
        )
        scores = condition_scores(source_rows)
        source_output: dict[str, Any] = {}
        for k in ks:
            base_selected = select_topk_by_subgraph(
                source_rows, scores["semantic_only"], k
            )
            method_selected = select_topk_by_subgraph(
                source_rows, scores["probabilistic_recalibrated"], k
            )
            per_context: list[tuple[int, int, int, int, int, int, int]] = []
            for subgraph_id in subgraphs:
                gt_keys = gt_by_subgraph.get(subgraph_id, set())
                base_rows = base_selected.get(subgraph_id, [])
                method_rows = method_selected.get(subgraph_id, [])
                base_keys = {exact_key_from_parts(row) for row in base_rows}
                method_keys = {exact_key_from_parts(row) for row in method_rows}
                per_context.append(
                    (
                        len(base_keys & gt_keys),
                        len(method_keys & gt_keys),
                        len(gt_keys),
                        sum(
                            row["attachment_policy_decision"] == "violated"
                            for row in base_rows
                        ),
                        sum(
                            row["attachment_policy_decision"] == "violated"
                            for row in method_rows
                        ),
                        len(base_rows),
                        len(method_rows),
                    )
                )
            data = np.asarray(per_context, dtype=np.float64)
            delta_r = np.empty(n_bootstrap, dtype=np.float64)
            delta_v = np.empty(n_bootstrap, dtype=np.float64)
            n_contexts = data.shape[0]
            for index in range(n_bootstrap):
                sample = data[rng.integers(0, n_contexts, size=n_contexts)]
                gt_den = sample[:, 2].sum()
                base_den = sample[:, 5].sum()
                method_den = sample[:, 6].sum()
                delta_r[index] = (
                    sample[:, 1].sum() / gt_den - sample[:, 0].sum() / gt_den
                    if gt_den > 0
                    else np.nan
                )
                delta_v[index] = (
                    sample[:, 4].sum() / method_den
                    - sample[:, 3].sum() / base_den
                    if base_den > 0 and method_den > 0
                    else np.nan
                )
            source_output[str(k)] = {
                "contexts": n_contexts,
                "delta_recall_ci95": percentile_ci(delta_r),
                "delta_violation_ci95": percentile_ci(delta_v),
            }
        output["sources"][source_name] = source_output
    return output


def gate_summary(
    metrics: dict[str, Any], method_name: str, paired: dict[str, Any]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for source_name, source in metrics["conditions"].items():
        semantic = source["conditions"]["source_score"]
        method = source["conditions"][method_name]
        source_result: dict[str, Any] = {}
        for k in (10, 50, 100):
            key = str(k)
            r0 = semantic["recall"]["by_k"][key]["recall"]
            r1 = method["recall"]["by_k"][key]["recall"]
            v0 = semantic["violation_rate"]["by_k"][key]["violation_rate"]
            v1 = method["violation_rate"]["by_k"][key]["violation_rate"]
            source_result[key] = {
                "source_score": {"recall": r0, "violation": v0},
                method_name: {"recall": r1, "violation": v1},
                "delta_recall": r1 - r0,
                "delta_violation": v1 - v0,
                "delta_recall_ci95": paired["sources"][source_name][key][
                    "delta_recall_ci95"
                ],
                "delta_violation_ci95": paired["sources"][source_name][key][
                    "delta_violation_ci95"
                ],
            }
            dr_ci = source_result[key]["delta_recall_ci95"]
            dv_ci = source_result[key]["delta_violation_ci95"]
            source_result[key]["development_gate_pass"] = bool(
                dr_ci[0] is not None
                and dv_ci[1] is not None
                and dr_ci[0] >= -0.01
                and dv_ci[1] < 0.0
            )
        result[source_name] = source_result
    return result


def report_text(
    diagnostics: dict[str, Any], counts: dict[str, Any], gates: dict[str, Any], method_name: str
) -> str:
    lines = [
        "# Attachment Subtype v2 Development Diagnostic",
        "",
        f"Status: `{STATUS}`",
        "",
        "This is a retrospective development diagnostic. It does not update the",
        "RelCompat3D main claim and is not an untouched or confirmatory result.",
        "",
        "## Fit",
        "",
    ]
    for predicate in PREDICATES:
        diag = diagnostics[predicate]
        c = diag["counts"]
        lines.extend(
            [
                f"- `{predicate}` train pos/neg: {c['train_positive']}/{c['train_negative']}; "
                f"dev pos/neg: {c['dev_positive']}/{c['dev_negative']}; "
                f"dev AUROC/Brier: {diag['dev']['auroc_valid']:.4f}/{diag['dev']['brier']:.4f}",
            ]
        )
    lines.extend(
        [
            "",
            "## Official-validation diagnostic",
            "",
            f"Scored rows: {counts['rows']}; fitted direct-route rows: "
            f"{counts['by_score_origin'].get('fitted_bidirectional_compatibility', 0)}; "
            f"neutral rows: {counts['by_score_origin'].get('neutral_fallback', 0)}.",
            "The gate requires paired-bootstrap dR CI lower bound >= -0.01 and "
            "dV CI upper bound < 0.",
            "",
            f"| Source | K | Source R/V | `{method_name}` R/V | dR | dV | Gate |",
            "|---|---:|---:|---:|---:|---:|:---:|",
        ]
    )
    for source_name, source_gates in gates.items():
        for k in (10, 50, 100):
            row = source_gates[str(k)]
            base = row["source_score"]
            method = row[method_name]
            lines.append(
                f"| {source_name} | {k} | {base['recall']:.4f}/{base['violation']:.4f} | "
                f"{method['recall']:.4f}/{method['violation']:.4f} | "
                f"{row['delta_recall']:+.4f} | {row['delta_violation']:+.4f} | "
                f"{'pass' if row['development_gate_pass'] else 'fail'} |"
            )
    lines.extend(
        [
            "",
            "The Violation diagnostic still uses the legacy attachment policy and",
            "therefore does not establish independent construct validity. A promotable",
            "v2 result requires the frozen mechanism review and a rebuilt target/verifier",
            "contract before model and source-evaluation hashes are locked.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--attachment-root",
        type=Path,
        default=Path(
            "archive/experiments/H001_geom_reliability/sources/attachment_deferred"
        ),
    )
    parser.add_argument(
        "--redesign-dir", type=Path, default=Path("subtype_redesign_v2")
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl"
        ),
    )
    parser.add_argument("--out", type=Path, default=Path("development_diagnostic_v1"))
    parser.add_argument("--epochs", type=int, default=800)
    parser.add_argument("--learning-rate", type=float, default=0.15)
    parser.add_argument("--l2", type=float, default=1e-4)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260713)
    parser.add_argument(
        "--fusion",
        choices=("raw_selective", "bounded_symmetric"),
        default="bounded_symmetric",
    )
    return parser.parse_args()


def resolve(base: Path, path: Path) -> Path:
    return path if path.is_absolute() else base / path


def main() -> None:
    args = parse_args()
    repo = args.repo_root.resolve()
    root = resolve(repo, args.attachment_root)
    redesign = resolve(root, args.redesign_dir)
    ground_truth_path = resolve(repo, args.ground_truth)
    out = resolve(redesign, args.out)
    out.mkdir(parents=True, exist_ok=True)

    training_rows = load_training_rows(root, redesign)
    model, diagnostics = fit_models(
        training_rows,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    write_json(out / "model.json", model)
    model_hash = sha256(out / "model.json")

    scored_rows, source_counts = load_scored_source_rows(root, model, args.fusion)
    ground_truth = list(iter_jsonl(ground_truth_path))
    denominator = read_json(root / "full_validation_protocol/denominator_audit.json")
    metrics, bootstrap = source_metrics(
        rows=scored_rows,
        ground_truth=ground_truth,
        denominator_audit=denominator,
        ks=[5, 10, 20, 50, 100],
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
    )
    rename_conditions(metrics, fusion=args.fusion)
    rename_conditions(bootstrap, fusion=args.fusion, bootstrap=True)
    metrics["schema_version"] = SCHEMA_VERSION
    metrics["status"] = STATUS
    bootstrap["schema_version"] = SCHEMA_VERSION
    bootstrap["status"] = STATUS
    method_name = condition_names(args.fusion)["probabilistic_recalibrated"]
    paired = paired_delta_bootstrap(
        scored_rows,
        ground_truth,
        ks=[5, 10, 20, 50, 100],
        n_bootstrap=args.n_bootstrap,
        seed=args.seed + 1,
    )
    gates = gate_summary(metrics, method_name, paired)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "paper_result": False,
        "retrospective_development_diagnostic": True,
        "model_sha256": model_hash,
        "fusion": args.fusion,
        "method_condition": method_name,
        "training_counts": {
            "rows": len(training_rows),
            "by_predicate": dict(
                sorted(Counter(row["predicate_label"] for row in training_rows).items())
            ),
            "by_split": dict(
                sorted(Counter(row["split_role"] for row in training_rows).items())
            ),
        },
        "source_counts": source_counts,
        "development_gates": gates,
        "limitations": [
            "The target subset is derived from the legacy policy-selected calibration route.",
            "Violation remains verifier-derived and is not an independent physical-validity label.",
            "The official validation target is used as a development diagnostic, not confirmation.",
            "Connected-to is neutral because direct versus mediated ontology is unresolved.",
        ],
    }
    write_json(out / "fit_diagnostics.json", diagnostics)
    write_json(out / "metrics.json", metrics)
    write_json(out / "bootstrap_ci.json", bootstrap)
    write_json(out / "paired_delta_ci.json", paired)
    write_json(out / "summary.json", summary)
    (out / "README.md").write_text(
        report_text(diagnostics, source_counts, gates, method_name), encoding="utf-8"
    )
    service = (
        "attachment_subtype_v2_bounded_diagnostic"
        if args.fusion == "bounded_symmetric"
        else "attachment_subtype_v2_development_diagnostic"
    )
    (out / "commands.md").write_text(
        "# Commands\n\n```bash\n"
        "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml "
        f"run --rm {service}\n"
        "```\n",
        encoding="utf-8",
    )

    errors: list[str] = []
    if len(training_rows) != 311:
        errors.append(f"training_rows:{len(training_rows)}!=311")
    if source_counts["rows"] != 190722:
        errors.append(f"source_rows:{source_counts['rows']}!=190722")
    forbidden = {"source_score", "source_rank", "source_id", "class_pair_prior"}
    for predicate_model in model["models"].values():
        feature_names = " ".join(predicate_model["spec"]["feature_names"])
        for name in forbidden:
            if name in feature_names:
                errors.append(f"forbidden_model_feature:{name}")
    validation = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if not errors else "failed",
        "validation_error_count": len(errors),
        "validation_errors": errors,
        "checks": {
            "training_rows": len(training_rows),
            "source_rows": source_counts["rows"],
            "source_score_used_in_fit": False,
            "class_prior_used_in_fit": False,
            "connected_to_bidirectional_model_fitted": False,
            "main_claim_changed": False,
        },
    }
    write_json(out / "validation.json", validation)
    output_names = [
        "README.md",
        "commands.md",
        "model.json",
        "fit_diagnostics.json",
        "metrics.json",
        "bootstrap_ci.json",
        "paired_delta_ci.json",
        "summary.json",
        "validation.json",
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS if not errors else "failed_validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_result": False,
        "model_fitted": True,
        "source_metrics_computed": True,
        "main_claim_changed": False,
        "inputs": {
            "migration_rows.jsonl": sha256(redesign / "migration_rows.jsonl"),
            "ground_truth.jsonl": sha256(ground_truth_path),
            "denominator_audit.json": sha256(
                root / "full_validation_protocol/denominator_audit.json"
            ),
        },
        "outputs": {
            name: {"sha256": sha256(out / name), "bytes": (out / name).stat().st_size}
            for name in output_names
        },
    }
    write_json(out / "manifest.json", manifest)
    if errors:
        raise SystemExit("validation_failed:" + ",".join(errors))
    print(
        json.dumps(
            {"status": STATUS, "out": str(out), "validation_errors": 0}
        )
    )


if __name__ == "__main__":
    main()
