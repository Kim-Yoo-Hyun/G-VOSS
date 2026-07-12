#!/usr/bin/env python3
"""Evaluate verifier-uncertainty sensitivity for frozen H001 rankings."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import run_reviewer_extension_metrics as base


SCHEMA_VERSION = "h001_uncertainty_sensitivity_v1"
KS = (5, 10, 20, 50, 100)
CONDITIONS = (
    "semantic_only",
    "family_conditional_risk",
    "pooled_calibration",
    "geometry_only_family",
    "rank_average_fusion",
    "reciprocal_rank_fusion",
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
    "sgfn_official_full_l160": {
        "predictions": "experiments/H001_geom_reliability/sources/sgfn/adapter/predictions.jsonl",
        "verification": "experiments/H001_geom_reliability/sources/sgfn/geometry/verification.jsonl",
        "ground_truth": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/uncertainty_sensitivity/frozen_v1"),
    )
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260712)
    return parser.parse_args()


def load_candidates(
    root: Path,
    source: str,
    spec: dict[str, str],
    evalmod: Any,
    family_model: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], int, int]:
    """Use the canonical pair when present, or the self-contained joined rows."""
    prediction_path = base.resolve(root, spec["predictions"])
    if prediction_path.exists():
        return base.load_candidates(root, source, spec, evalmod, family_model)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    verification_path = base.resolve(root, spec["verification"])
    input_count = 0
    with verification_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank_joined_row:{source}:{line_no}")
            row = json.loads(line)
            input_count += 1
            family = row["predicate"]["predicate_family"]
            if family not in base.FAMILIES:
                continue
            compact = evalmod.compact_verification(row)
            prediction = dict(row)
            prediction["scores"] = dict(row.get("semantic") or {})
            semantic = evalmod.semantic_score(prediction)
            pooled = evalmod.p_geom_valid_from_verification(compact)
            family_probability = evalmod.family_specific_p_geom_valid(prediction, compact, family_model)
            if semantic is None or pooled is None or family_probability is None:
                raise ValueError(f"missing_score:{source}:{row['prediction_id']}")
            grouped[row["subgraph_id"]].append(
                {
                    "prediction_id": row["prediction_id"],
                    "key": base.prediction_key(prediction),
                    "subgraph_id": row["subgraph_id"],
                    "family": family,
                    "semantic": float(semantic),
                    "p_pooled": float(pooled),
                    "p_family": float(family_probability),
                    "status": compact.get("verification_status"),
                    "scores": {},
                }
            )
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
            }
    in_scope = sum(len(rows) for rows in grouped.values())
    print(json.dumps({"source": source, "input_rows": input_count, "in_scope_rows": in_scope, "fallback": "self_contained_verification_rows"}))
    return grouped, input_count, in_scope


def ratio(num: np.ndarray, den: np.ndarray) -> float | None:
    return float(num.sum() / den.sum()) if den.sum() > 0 else None


def bootstrap_ratio(
    num: np.ndarray, den: np.ndarray, indices: np.ndarray
) -> tuple[list[float | None], np.ndarray]:
    sampled_num = num[indices].sum(axis=1)
    sampled_den = den[indices].sum(axis=1)
    samples = np.divide(
        sampled_num,
        sampled_den,
        out=np.full_like(sampled_num, np.nan, dtype=np.float64),
        where=sampled_den > 0,
    )
    finite = samples[np.isfinite(samples)]
    ci = [float(value) for value in np.percentile(finite, [2.5, 97.5])] if len(finite) else [None, None]
    return ci, samples


def summarize_counts(counts: dict[str, np.ndarray], indices: np.ndarray) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    satisfied = counts["satisfied"]
    uncertain = counts["uncertain"]
    violated = counts["violated"]
    selected = counts["selected"]
    status_total = satisfied + uncertain + violated
    decidable = satisfied + violated
    definitions = {
        "violation_all": (violated, status_total),
        "violation_decidable": (violated, decidable),
        "uncertainty_rate": (uncertain, status_total),
        "decidable_coverage": (decidable, status_total),
        "pessimistic_violation": (violated + uncertain, status_total),
        "status_coverage": (status_total, selected),
    }
    output: dict[str, Any] = {
        "counts": {
            "selected": int(selected.sum()),
            "satisfied": int(satisfied.sum()),
            "uncertain": int(uncertain.sum()),
            "violated": int(violated.sum()),
            "other_or_missing": int((selected - status_total).sum()),
        }
    }
    samples: dict[str, np.ndarray] = {}
    for name, (numerator, denominator) in definitions.items():
        ci, metric_samples = bootstrap_ratio(numerator, denominator, indices)
        output[name] = {"point": ratio(numerator, denominator), "ci95": ci}
        samples[name] = metric_samples
    return output, samples


def make_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# H001 Uncertainty Sensitivity",
        "",
        f"Status: `{report['status']}`",
        "",
        "`violation_all` is the reported verifier V with uncertain rows in the denominator; "
        "`violation_decidable` conditions on satisfied/violated rows; `pessimistic_violation` "
        "counts every uncertain row as a violation.",
        "",
        "## K=100 diagnostic",
        "",
        "| source | condition | V-all | V-decidable | uncertain | pessimistic V | decidable coverage |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source, source_data in report["sources"].items():
        for condition in CONDITIONS:
            row = source_data["conditions"][condition]["100"]
            lines.append(
                "| {source} | {condition} | {va:.4f} | {vd:.4f} | {ur:.4f} | {pv:.4f} | {dc:.4f} |".format(
                    source=source,
                    condition=condition,
                    va=row["violation_all"]["point"],
                    vd=row["violation_decidable"]["point"],
                    ur=row["uncertainty_rate"]["point"],
                    pv=row["pessimistic_violation"]["point"],
                    dc=row["decidable_coverage"]["point"],
                )
            )
    lines.extend(
        [
            "",
            "All intervals and paired deltas use the same 1,000 subgraph-bootstrap indices within each source. "
            "This analysis does not change any score, rank, family, or verifier status.",
            "",
        ]
    )
    return "\n".join(lines)


def csv_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source, source_data in report["sources"].items():
        for condition in CONDITIONS:
            for k in KS:
                value = source_data["conditions"][condition][str(k)]
                row: dict[str, Any] = {"source": source, "condition": condition, "k": k, **value["counts"]}
                for metric in (
                    "violation_all",
                    "violation_decidable",
                    "uncertainty_rate",
                    "decidable_coverage",
                    "pessimistic_violation",
                    "status_coverage",
                ):
                    row[metric] = value[metric]["point"]
                    row[f"{metric}_ci95_low"] = value[metric]["ci95"][0]
                    row[f"{metric}_ci95_high"] = value[metric]["ci95"][1]
                rows.append(row)
    return rows


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = base.resolve(root, args.out)
    evalmod = base.load_eval_module(root)
    family_model = base.read_json(
        root
        / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json"
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready_frozen_verifier_uncertainty_sensitivity",
        "n_bootstrap": args.n_bootstrap,
        "seed": args.seed,
        "bootstrap_unit": "subgraph_id",
        "conditions": list(CONDITIONS),
        "sources": {},
        "claim_boundary": "Verifier-status sensitivity only; no independent human-validity claim.",
    }
    for source_index, (source, spec) in enumerate(SOURCE_SPECS.items()):
        grouped, input_count, in_scope = load_candidates(root, source, spec, evalmod, family_model)
        subgraphs = sorted(grouped)
        rng = np.random.default_rng(args.seed + source_index)
        indices = rng.integers(0, len(subgraphs), size=(args.n_bootstrap, len(subgraphs)))
        source_output: dict[str, Any] = {
            "input_rows": input_count,
            "in_scope_rows": in_scope,
            "subgraphs": len(subgraphs),
            "inputs": spec,
            "conditions": {},
            "paired_deltas_vs_semantic": {},
        }
        metric_samples: dict[str, dict[str, dict[str, np.ndarray]]] = defaultdict(dict)
        for condition in CONDITIONS:
            source_output["conditions"][condition] = {}
            for k in KS:
                counts = {
                    name: np.zeros(len(subgraphs), dtype=np.float64)
                    for name in ("selected", "satisfied", "uncertain", "violated")
                }
                for index, subgraph in enumerate(subgraphs):
                    ranked = sorted(
                        grouped[subgraph], key=lambda row: (-row["scores"][condition], row["key"])
                    )[:k]
                    counts["selected"][index] = len(ranked)
                    for row in ranked:
                        if row["status"] in {"satisfied", "uncertain", "violated"}:
                            counts[row["status"]][index] += 1
                summary, samples = summarize_counts(counts, indices)
                source_output["conditions"][condition][str(k)] = summary
                metric_samples[condition][str(k)] = samples
        reference = "semantic_only"
        for condition in CONDITIONS:
            if condition == reference:
                continue
            source_output["paired_deltas_vs_semantic"][condition] = {}
            for k in KS:
                source_output["paired_deltas_vs_semantic"][condition][str(k)] = {}
                for metric in metric_samples[condition][str(k)]:
                    point = (
                        source_output["conditions"][condition][str(k)][metric]["point"]
                        - source_output["conditions"][reference][str(k)][metric]["point"]
                    )
                    delta = metric_samples[condition][str(k)][metric] - metric_samples[reference][str(k)][metric]
                    finite = delta[np.isfinite(delta)]
                    source_output["paired_deltas_vs_semantic"][condition][str(k)][metric] = {
                        "point": point,
                        "ci95": [float(value) for value in np.percentile(finite, [2.5, 97.5])],
                    }
        report["sources"][source] = source_output

    out.mkdir(parents=True, exist_ok=True)
    base.write_json(out / "summary.json", report)
    (out / "summary.md").write_text(make_markdown(report), encoding="utf-8")
    rows = csv_rows(report)
    with (out / "metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    base.write_json(
        out / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": report["created_at_utc"],
            "status": report["status"],
            "outputs": [
                base.relpath(root, out / "summary.json"),
                base.relpath(root, out / "summary.md"),
                base.relpath(root, out / "metrics.csv"),
            ],
            "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm uncertainty_sensitivity",
        },
    )
    print(json.dumps({"status": report["status"], "sources": list(report["sources"]), "out": base.relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
