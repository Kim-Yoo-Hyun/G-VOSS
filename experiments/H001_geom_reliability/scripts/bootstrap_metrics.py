#!/usr/bin/env python3
"""Subgraph bootstrap CIs for H001 prediction metrics.

The main metric runner reports deterministic point estimates. This script keeps
the same row contract, condition scoring, and denominator semantics, then
resamples evaluation subgraphs to estimate uncertainty for the paper tables.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "h001_bootstrap_ci_v1"
DEFAULT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
DEFAULT_KS = (50, 100)
DEFAULT_CONDITIONS = (
    "semantic_only",
    "probabilistic_recalibrated",
    "rule_verified_point_subtype",
    "control_family_specific_p_geom_valid",
)


@dataclass(frozen=True)
class SourceSpec:
    name: str
    predictions_jsonl: Path
    ground_truth_jsonl: Path
    verification_jsonl: Path
    metrics_json: Path
    family_model_json: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap H001 source metrics by subgraph.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/bootstrap_ci"),
    )
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260526)
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--ks", nargs="+", type=int, default=list(DEFAULT_KS))
    parser.add_argument(
        "--open3dsg-source-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg"),
        help="Open3DSG source artifact root containing adapter/, geometry/, and metrics/.",
    )
    parser.add_argument("--open3dsg-source-name", default="open3dsg_ov")
    parser.add_argument(
        "--vlsat-source-root",
        type=Path,
        help=(
            "Optional VL-SAT source artifact root containing adapter/, geometry/, "
            "and metrics/. If omitted, use the locked 127-scan hardened artifacts."
        ),
    )
    parser.add_argument("--vlsat-source-name", default="vlsat_closed_set")
    parser.add_argument(
        "--vlsat-metrics-json",
        type=Path,
        help="Optional metrics JSON override for the VL-SAT source.",
    )
    parser.add_argument(
        "--open3dsg-metrics-json",
        type=Path,
        help="Optional metrics JSON override for the Open3DSG source.",
    )
    parser.add_argument(
        "--skip-open3dsg",
        action="store_true",
        help="Bootstrap only the VL-SAT source. Use for VL-SAT-only full-validation gates.",
    )
    parser.add_argument(
        "--docker-service-name",
        help="Optional compose service name to record in the manifest command.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def load_eval_module(repo_root: Path) -> Any:
    module_path = (
        repo_root
        / "hypothesis/CAND-001/H001_geometry-grounded-verification/tools/evaluate_predictions.py"
    )
    spec = importlib.util.spec_from_file_location("h001_evaluate_predictions", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import metric module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def source_specs(
    repo_root: Path,
    open3dsg_root_arg: Path,
    open3dsg_source_name: str,
    open3dsg_metrics_json_arg: Path | None,
    vlsat_root_arg: Path | None,
    vlsat_source_name: str,
    vlsat_metrics_json_arg: Path | None,
    skip_open3dsg: bool,
) -> list[SourceSpec]:
    hroot = repo_root / "hypothesis/CAND-001/H001_geometry-grounded-verification"
    open3dsg_root = open3dsg_root_arg if open3dsg_root_arg.is_absolute() else repo_root / open3dsg_root_arg
    family_model = hroot / "artifacts/calibration/p_geom_valid_family/model.json"
    vlsat_metrics_json = (
        vlsat_metrics_json_arg
        if vlsat_metrics_json_arg is None or vlsat_metrics_json_arg.is_absolute()
        else repo_root / vlsat_metrics_json_arg
    )
    open3dsg_metrics_json = (
        open3dsg_metrics_json_arg
        if open3dsg_metrics_json_arg is None or open3dsg_metrics_json_arg.is_absolute()
        else repo_root / open3dsg_metrics_json_arg
    )
    if vlsat_root_arg is None:
        gt = hroot / "artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
        vlsat_spec = SourceSpec(
            name=vlsat_source_name,
            predictions_jsonl=hroot / "artifacts/evaluation/vlsat_closed_set/hardened/predictions.jsonl",
            ground_truth_jsonl=gt,
            verification_jsonl=hroot
            / "artifacts/evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl",
            metrics_json=vlsat_metrics_json
            or hroot / "artifacts/evaluation/vlsat_closed_set/hardened_g3/metrics.json",
            family_model_json=family_model,
        )
    else:
        vlsat_root = vlsat_root_arg if vlsat_root_arg.is_absolute() else repo_root / vlsat_root_arg
        gt = vlsat_root / "adapter/ground_truth.jsonl"
        vlsat_spec = SourceSpec(
            name=vlsat_source_name,
            predictions_jsonl=vlsat_root / "adapter/predictions.jsonl",
            ground_truth_jsonl=gt,
            verification_jsonl=vlsat_root / "geometry/verification.jsonl",
            metrics_json=vlsat_metrics_json or vlsat_root / "metrics/metrics.json",
            family_model_json=family_model,
        )
    specs = [vlsat_spec]
    if not skip_open3dsg:
        specs.append(
            SourceSpec(
                name=open3dsg_source_name,
                predictions_jsonl=open3dsg_root / "adapter/predictions.jsonl",
                ground_truth_jsonl=gt,
                verification_jsonl=open3dsg_root / "geometry/verification.jsonl",
                metrics_json=open3dsg_metrics_json or open3dsg_root / "metrics/metrics.json",
                family_model_json=family_model,
            )
        )
    return specs


def metric_reference(metrics: dict[str, Any], condition: str, metric: str, k: int) -> float | None:
    data = metrics.get("conditions", {}).get(condition, {})
    if metric == "recall":
        value = data.get("recall", {}).get("by_k", {}).get(str(k), {}).get("recall")
    elif metric == "violation_rate":
        value = data.get("violation_rate", {}).get("by_k", {}).get(str(k), {}).get(
            "violation_rate"
        )
    else:
        raise ValueError(metric)
    if value is None:
        return None
    return float(value)


def finite_ratio(num: float, den: float) -> float:
    if den <= 0:
        return math.nan
    return float(num) / float(den)


def percentile_summary(values: np.ndarray, point: float) -> dict[str, Any]:
    valid = values[np.isfinite(values)]
    if len(valid) == 0:
        return {"point": point, "median": None, "ci95": [None, None], "valid_samples": 0}
    lower, median, upper = np.percentile(valid, [2.5, 50.0, 97.5])
    return {
        "point": point,
        "median": float(median),
        "ci95": [float(lower), float(upper)],
        "valid_samples": int(len(valid)),
    }


def status_for(evalmod: Any, verification_by_id: dict[str, dict[str, Any]], row: dict[str, Any], variant: str | None) -> str | None:
    verification = verification_by_id.get(row["prediction_id"])
    if verification is None:
        return None
    return evalmod.verification_status(verification, variant)


def condition_predictions(
    evalmod: Any,
    predictions: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    families: set[str],
    family_model: dict[str, Any] | None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str | None], list[str]]:
    warnings: list[str] = []
    conditions: dict[str, list[dict[str, Any]]] = {"semantic_only": predictions}
    violation_variants: dict[str, str | None] = {"semantic_only": None}

    recalibrated, _, errors = evalmod.recalibrated_predictions(
        predictions, verification_by_id, families
    )
    conditions["probabilistic_recalibrated"] = recalibrated
    violation_variants["probabilistic_recalibrated"] = None
    warnings.extend(f"probabilistic_recalibrated:{error}" for error in errors)

    rule, _ = evalmod.apply_rule_filter(
        predictions,
        verification_by_id,
        policy="filter_safe",
        variant="point_subtype",
    )
    conditions["rule_verified_point_subtype"] = rule
    violation_variants["rule_verified_point_subtype"] = "point_subtype"

    family_specific, _, errors = evalmod.ablation_control_predictions(
        predictions,
        verification_by_id,
        families,
        "family_specific_p_geom_valid",
        family_specific_model=family_model,
    )
    conditions["control_family_specific_p_geom_valid"] = family_specific
    violation_variants["control_family_specific_p_geom_valid"] = None
    warnings.extend(f"control_family_specific_p_geom_valid:{error}" for error in errors)

    return conditions, violation_variants, warnings


def subgraph_contributions(
    evalmod: Any,
    predictions: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    families: set[str],
    ks: list[int],
    violation_variant: str | None,
) -> tuple[list[str], dict[str, dict[str, np.ndarray]]]:
    gt_by_subgraph: dict[str, set[tuple[Any, ...]]] = defaultdict(set)
    for row in ground_truth:
        if evalmod.in_scope_gt(row, families):
            gt_by_subgraph[row["subgraph_id"]].add(evalmod.gt_key(row))

    scoped_predictions = [row for row in predictions if evalmod.in_scope_prediction(row, families)]
    grouped = evalmod.sorted_by_subgraph(scoped_predictions)
    subgraph_ids = sorted(set(gt_by_subgraph) | set(grouped))

    output: dict[str, dict[str, np.ndarray]] = {}
    for k in ks:
        recall_num: list[int] = []
        recall_den: list[int] = []
        violation_num: list[int] = []
        violation_den: list[int] = []
        for subgraph_id in subgraph_ids:
            gt_keys = gt_by_subgraph.get(subgraph_id, set())
            selected = grouped.get(subgraph_id, [])[:k]
            selected_keys = {evalmod.prediction_key(row) for row in selected}
            statuses = [
                status_for(evalmod, verification_by_id, row, violation_variant)
                for row in selected
                if row["prediction_id"] in verification_by_id
            ]
            valid_statuses = [
                status for status in statuses if status in {"satisfied", "uncertain", "violated"}
            ]
            recall_num.append(len(selected_keys & gt_keys))
            recall_den.append(len(gt_keys))
            violation_num.append(sum(1 for status in valid_statuses if status == "violated"))
            violation_den.append(len(valid_statuses))
        output[str(k)] = {
            "recall_num": np.asarray(recall_num, dtype=np.float64),
            "recall_den": np.asarray(recall_den, dtype=np.float64),
            "violation_num": np.asarray(violation_num, dtype=np.float64),
            "violation_den": np.asarray(violation_den, dtype=np.float64),
        }
    return subgraph_ids, output


def bootstrap_ratios(
    values: dict[str, np.ndarray],
    sample_indices: np.ndarray,
    metric: str,
) -> tuple[float, np.ndarray]:
    if metric == "recall":
        num = values["recall_num"]
        den = values["recall_den"]
    elif metric == "violation_rate":
        num = values["violation_num"]
        den = values["violation_den"]
    else:
        raise ValueError(metric)
    point = finite_ratio(float(num.sum()), float(den.sum()))
    sampled_num = num[sample_indices].sum(axis=1)
    sampled_den = den[sample_indices].sum(axis=1)
    ratios = sampled_num / sampled_den
    ratios[sampled_den <= 0] = math.nan
    return point, ratios


def analyze_source(
    evalmod: Any,
    repo_root: Path,
    spec: SourceSpec,
    families: set[str],
    ks: list[int],
    n_bootstrap: int,
    seed: int,
) -> dict[str, Any]:
    predictions = evalmod.load_jsonl(spec.predictions_jsonl)
    ground_truth = evalmod.load_jsonl(spec.ground_truth_jsonl)
    verification_by_id = evalmod.load_verification(spec.verification_jsonl)
    metrics = load_json(spec.metrics_json)
    family_model = load_json(spec.family_model_json) if spec.family_model_json else None
    warnings: list[str] = []

    conditions, violation_variants, condition_warnings = condition_predictions(
        evalmod, predictions, verification_by_id, families, family_model
    )
    warnings.extend(condition_warnings)

    condition_contribs: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    population: list[str] | None = None
    for condition, condition_rows in conditions.items():
        subgraph_ids, contribs = subgraph_contributions(
            evalmod,
            condition_rows,
            ground_truth,
            verification_by_id,
            families,
            ks,
            violation_variants[condition],
        )
        if population is None:
            population = subgraph_ids
        elif population != subgraph_ids:
            warnings.append(f"{condition}:population_mismatch")
        condition_contribs[condition] = contribs

    if population is None or not population:
        raise RuntimeError(f"No bootstrap population for {spec.name}")

    rng = np.random.default_rng(seed)
    sample_indices = rng.integers(0, len(population), size=(n_bootstrap, len(population)))

    result: dict[str, Any] = {
        "source": spec.name,
        "status": "ready",
        "input_rows": {
            "predictions": len(predictions),
            "ground_truth": len(ground_truth),
            "verification": len(verification_by_id),
        },
        "families": sorted(families),
        "population": {
            "unit": "subgraph_id",
            "subgraphs": len(population),
        },
        "inputs": {
            "predictions_jsonl": relpath(repo_root, spec.predictions_jsonl),
            "ground_truth_jsonl": relpath(repo_root, spec.ground_truth_jsonl),
            "verification_jsonl": relpath(repo_root, spec.verification_jsonl),
            "metrics_json": relpath(repo_root, spec.metrics_json),
            "family_model_json": relpath(repo_root, spec.family_model_json)
            if spec.family_model_json
            else None,
        },
        "conditions": {},
        "deltas_vs_semantic_only": {},
        "warnings": warnings,
    }

    sampled_metrics: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    point_metrics: dict[str, dict[str, dict[str, float]]] = {}
    for condition, contribs in condition_contribs.items():
        sampled_metrics[condition] = {}
        point_metrics[condition] = {}
        result["conditions"][condition] = {}
        for k in ks:
            key = str(k)
            result["conditions"][condition][key] = {}
            sampled_metrics[condition][key] = {}
            point_metrics[condition][key] = {}
            for metric_name in ("recall", "violation_rate"):
                point, samples = bootstrap_ratios(contribs[key], sample_indices, metric_name)
                ref = metric_reference(metrics, condition, metric_name, k)
                if ref is not None and math.isfinite(point) and abs(point - ref) > 1e-10:
                    warnings.append(
                        f"{condition}:K{k}:{metric_name}:point_mismatch:"
                        f"computed={point}:metrics_json={ref}"
                    )
                sampled_metrics[condition][key][metric_name] = samples
                point_metrics[condition][key][metric_name] = point
                result["conditions"][condition][key][metric_name] = percentile_summary(
                    samples, point
                )
                result["conditions"][condition][key][metric_name]["metrics_json_point"] = ref

    semantic = "semantic_only"
    for condition in conditions:
        if condition == semantic:
            continue
        result["deltas_vs_semantic_only"][condition] = {}
        for k in ks:
            key = str(k)
            result["deltas_vs_semantic_only"][condition][key] = {}
            for metric_name in ("recall", "violation_rate"):
                point = (
                    point_metrics[condition][key][metric_name]
                    - point_metrics[semantic][key][metric_name]
                )
                samples = (
                    sampled_metrics[condition][key][metric_name]
                    - sampled_metrics[semantic][key][metric_name]
                )
                summary = percentile_summary(samples, point)
                valid = samples[np.isfinite(samples)]
                if len(valid):
                    summary["prob_delta_le_0"] = float(np.mean(valid <= 0.0))
                    summary["prob_delta_ge_0"] = float(np.mean(valid >= 0.0))
                else:
                    summary["prob_delta_le_0"] = None
                    summary["prob_delta_ge_0"] = None
                result["deltas_vs_semantic_only"][condition][key][metric_name] = summary

    if warnings:
        result["status"] = "ready_with_warnings"
    return result


def pct(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{100.0 * value:.2f}%"


def pp(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{100.0 * value:+.2f} pp"


def ci(summary: dict[str, Any], formatter: Any) -> str:
    lower, upper = summary.get("ci95", [None, None])
    return f"[{formatter(lower)}, {formatter(upper)}]"


def make_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# H001 Bootstrap CI",
        "",
        f"Created at UTC: `{report['created_at_utc']}`",
        f"Status: `{report['status']}`",
        f"Bootstrap samples: `{report['n_bootstrap']}`",
        f"Seed: `{report['seed']}`",
        "",
        (
            "Subgraphs are resampled with replacement. Point estimates are recomputed "
            "from the same per-subgraph contributions used for the bootstrap and checked "
            "against the locked metrics JSON."
        ),
        "",
        "| source | condition | K | R@K point | R@K 95% CI | V@K point | V@K 95% CI | dR vs semantic | dV vs semantic |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source_name, source in report["sources"].items():
        for condition, by_k in source["conditions"].items():
            for k in sorted(by_k, key=lambda item: int(item)):
                recall = by_k[k]["recall"]
                violation = by_k[k]["violation_rate"]
                delta = source["deltas_vs_semantic_only"].get(condition, {}).get(k, {})
                delta_recall = delta.get("recall", {}).get("point")
                delta_violation = delta.get("violation_rate", {}).get("point")
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            source_name,
                            condition,
                            k,
                            pct(recall["point"]),
                            ci(recall, pct),
                            pct(violation["point"]),
                            ci(violation, pct),
                            pp(delta_recall),
                            pp(delta_violation),
                        ]
                    )
                    + " |"
                )
    lines.extend(["", "## Warnings", ""])
    any_warning = False
    for source_name, source in report["sources"].items():
        for warning in source.get("warnings", []):
            any_warning = True
            lines.append(f"- `{source_name}`: `{warning}`")
    if not any_warning:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = args.out.resolve()
    families = set(args.families)
    ks = list(args.ks)
    evalmod = load_eval_module(repo_root)
    bootstrap_service = args.docker_service_name or (
        "bootstrap_ci_full_validation_vlsat"
        if args.vlsat_source_root is not None and args.skip_open3dsg
        else "bootstrap_ci"
    )

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
        "seed": args.seed,
        "n_bootstrap": args.n_bootstrap,
        "families": sorted(families),
        "ks": ks,
        "bootstrap_unit": "subgraph_id",
        "conditions": list(DEFAULT_CONDITIONS),
        "sources": {},
        "docker_command": (
            "UID=$(id -u) GID=$(id -g) docker compose -f "
            f"experiments/H001_geom_reliability/compose.yaml run --rm {bootstrap_service}"
        ),
    }

    for spec in source_specs(
        repo_root=repo_root,
        open3dsg_root_arg=args.open3dsg_source_root,
        open3dsg_source_name=args.open3dsg_source_name,
        open3dsg_metrics_json_arg=args.open3dsg_metrics_json,
        vlsat_root_arg=args.vlsat_source_root,
        vlsat_source_name=args.vlsat_source_name,
        vlsat_metrics_json_arg=args.vlsat_metrics_json,
        skip_open3dsg=args.skip_open3dsg,
    ):
        missing = [
            path
            for path in [
                spec.predictions_jsonl,
                spec.ground_truth_jsonl,
                spec.verification_jsonl,
                spec.metrics_json,
                spec.family_model_json,
            ]
            if path is not None and not path.exists()
        ]
        if missing:
            report["sources"][spec.name] = {
                "source": spec.name,
                "status": "blocked_missing_inputs",
                "missing": [relpath(repo_root, path) for path in missing],
            }
            report["status"] = "blocked_missing_inputs"
            continue
        source_result = analyze_source(
            evalmod=evalmod,
            repo_root=repo_root,
            spec=spec,
            families=families,
            ks=ks,
            n_bootstrap=args.n_bootstrap,
            seed=args.seed,
        )
        report["sources"][spec.name] = source_result
        if source_result["status"] != "ready":
            report["status"] = "ready_with_warnings"

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "summary.json", report)
    (out_dir / "summary.md").write_text(make_markdown(report), encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": report["created_at_utc"],
        "status": report["status"],
        "output_files": [
            relpath(repo_root, out_dir / "summary.json"),
            relpath(repo_root, out_dir / "summary.md"),
        ],
        "docker_command": report["docker_command"],
        "n_bootstrap": args.n_bootstrap,
        "seed": args.seed,
    }
    write_json(out_dir / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": report["status"],
                "sources": sorted(report["sources"].keys()),
                "out": relpath(repo_root, out_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if report["status"] in {"ready", "ready_with_warnings"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
