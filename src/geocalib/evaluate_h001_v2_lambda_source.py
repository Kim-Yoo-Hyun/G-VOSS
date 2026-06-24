#!/usr/bin/env python3
"""Evaluate H001_v2 lambda-soft source metrics under a separate artifact root."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import evaluate_predictions as h001_eval
from paths import REPO_ROOT, repo_rel


SCHEMA_VERSION = "h001_v2_lambda_source_eval_v1"
DEFAULT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
DEFAULT_KS = (5, 10, 20, 50, 100)
DEFAULT_LAMBDA_POLICY = (
    Path("hypothesis/CAND-001/H001_v2_risk_controlled_reranking")
    / "artifacts/calibration_lambda_selection/lambda_policy.json"
)
READ_ONLY_ROOTS = (
    Path("experiments/H001_geom_reliability/sources/vlsat/full_validation"),
    Path(
        "experiments/H001_geom_reliability/sources/open3dsg/full_validation/"
        "recovery_relaxed_views_min2"
    ),
    Path(
        "archive/hypothesis_records/hypothesis/CAND-001/"
        "H001_geometry-grounded-verification"
    ),
    Path("results/h001_geom_reliability"),
    Path("paper"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate H001_v2 lambda-soft source metrics."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--predictions-jsonl", type=Path, required=True)
    parser.add_argument("--ground-truth-jsonl", type=Path, required=True)
    parser.add_argument("--verification-jsonl", type=Path, required=True)
    parser.add_argument("--lambda-policy-json", type=Path, default=DEFAULT_LAMBDA_POLICY)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--ks", nargs="+", type=int, default=list(DEFAULT_KS))
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def assert_writable_output(repo_root: Path, output_dir: Path, overwrite: bool) -> None:
    output_resolved = output_dir.resolve()
    for root in READ_ONLY_ROOTS:
        root_resolved = (repo_root / root).resolve()
        try:
            output_resolved.relative_to(root_resolved)
        except ValueError:
            continue
        raise ValueError(
            "Refusing to write H001_v2 lambda source-eval outputs under read-only root: "
            f"{repo_rel(output_dir, repo_root)}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"Output directory is non-empty: {repo_rel(output_dir, repo_root)}. "
                "Pass --overwrite to replace this H001_v2 lambda source-eval output."
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def load_lambda_policy(path: Path) -> dict[str, Any]:
    data = h001_eval.load_json(path)
    if data.get("status") != "ready":
        raise ValueError(f"Lambda policy is not ready: {path}")
    lam = h001_eval.finite_float(data.get("lambda_star"))
    if lam is None or lam < 0:
        raise ValueError(f"Lambda policy lacks a nonnegative lambda_star: {path}")
    return data


def in_scope_predictions(predictions: list[dict[str, Any]], families: set[str]) -> list[dict[str, Any]]:
    return [row for row in predictions if h001_eval.in_scope_prediction(row, families)]


def summarize_counts_by_family(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["predicate"]["predicate_family"] for row in rows).items()))


def selected_count_summary(
    predictions: list[dict[str, Any]],
    ks: list[int],
    families: set[str],
) -> dict[str, Any]:
    scoped = in_scope_predictions(predictions, families)
    grouped = h001_eval.sorted_by_subgraph(scoped)
    by_k: dict[str, Any] = {}
    for k in ks:
        counts = [min(len(rows), k) for rows in grouped.values()]
        expected = len(grouped) * k
        selected = sum(counts)
        by_k[str(k)] = {
            "subgraphs_with_eligible": len(grouped),
            "selected_predictions": selected,
            "full_k_capacity": expected,
            "capacity_ratio": selected / expected if expected else None,
            "subgraphs_below_k": sum(1 for count in counts if count < k),
        }
    return {
        "in_scope_predictions": len(scoped),
        "subgraphs_with_eligible": len(grouped),
        "by_k": by_k,
        "by_family": summarize_counts_by_family(scoped),
    }


def status_counts_for(
    rows: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        status = h001_eval.verification_status(verification_by_id.get(row["prediction_id"]))
        counts[str(status)] += 1
    return dict(sorted(counts.items()))


def lambda_soft_predictions(
    predictions: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    families: set[str],
    lam: float,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    output: list[dict[str, Any]] = []
    errors: list[str] = []
    counts: Counter[str] = Counter()
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    p_values: list[float] = []
    scores: list[float] = []

    for row in predictions:
        family = row["predicate"]["predicate_family"]
        if family not in families:
            output.append(row)
            continue
        counts["in_scope_predictions"] += 1
        by_family[family]["in_scope_predictions"] += 1
        verification = verification_by_id.get(row["prediction_id"])
        if verification is None:
            counts["missing_verification"] += 1
            by_family[family]["missing_verification"] += 1
            output.append(row)
            continue
        p_geom_valid = h001_eval.p_geom_valid_from_verification(verification)
        semantic = h001_eval.semantic_score(row)
        if p_geom_valid is None:
            counts["missing_p_geom_valid"] += 1
            by_family[family]["missing_p_geom_valid"] += 1
            output.append(row)
            continue
        if semantic is None:
            counts["missing_semantic_score"] += 1
            by_family[family]["missing_semantic_score"] += 1
            output.append(row)
            continue
        score = semantic * (p_geom_valid**lam)
        status = h001_eval.verification_status(verification)
        counts[f"scored_status_{status}"] += 1
        by_family[family][f"scored_status_{status}"] += 1
        counts["scored_predictions"] += 1
        by_family[family]["scored_predictions"] += 1
        p_values.append(p_geom_valid)
        scores.append(score)
        output.append(
            h001_eval.copy_with_ranking_score(
                row,
                score,
                "semantic_ranking_score*p_geom_valid^lambda",
                extra_scores={
                    "p_geom_valid": p_geom_valid,
                    "h001_v2_lambda_star": lam,
                    "h001_v2_geometry_penalty": p_geom_valid**lam,
                },
            )
        )

    if counts.get("missing_verification"):
        errors.append(f"missing_verification:{counts['missing_verification']}")
    if counts.get("missing_p_geom_valid"):
        errors.append(f"missing_p_geom_valid:{counts['missing_p_geom_valid']}")
    if counts.get("missing_semantic_score"):
        errors.append(f"missing_semantic_score:{counts['missing_semantic_score']}")
    summary = {
        "policy": "h001_v2_lambda_soft_reranking",
        "selection_rule": "score = semantic_score * p_geom_valid^lambda_star",
        "lambda_star": lam,
        "score_formula": "semantic_ranking_score*p_geom_valid^lambda",
        "counts": dict(sorted(counts.items())),
        "by_family": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(by_family.items())
        },
        "p_geom_valid": h001_eval.summarize_values(p_values),
        "lambda_soft_score": h001_eval.summarize_values(scores),
    }
    return output, summary, errors


def lambda_control_predictions(
    predictions: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    families: set[str],
    lam: float,
    control_name: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    if control_name == "shuffled_geometry_lambda":
        donor_map = h001_eval.shifted_p_geom_by_family(
            predictions,
            verification_by_id,
            families,
        )
        donor_field = "shuffled_geometry_p_geom_valid"
        shuffle_policy = "deterministic_half_rotation_within_predicate_family"
    elif control_name == "wrong_pair_geometry_lambda":
        donor_map = h001_eval.shifted_p_geom_by_wrong_pair(
            predictions,
            verification_by_id,
            families,
        )
        donor_field = "wrong_pair_geometry_p_geom_valid"
        shuffle_policy = "deterministic_rotation_within_subgraph_family_different_pair"
    else:
        raise ValueError(f"unknown_lambda_control:{control_name}")

    output: list[dict[str, Any]] = []
    errors: list[str] = []
    counts: Counter[str] = Counter()
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    donor_values: list[float] = []
    scores: list[float] = []

    for row in predictions:
        family = row["predicate"]["predicate_family"]
        if family not in families:
            output.append(row)
            continue
        counts["in_scope_predictions"] += 1
        by_family[family]["in_scope_predictions"] += 1
        donor_p = h001_eval.finite_float(donor_map.get(row["prediction_id"]))
        semantic = h001_eval.semantic_score(row)
        if donor_p is None:
            counts["missing_control_p_geom_valid"] += 1
            by_family[family]["missing_control_p_geom_valid"] += 1
            output.append(row)
            continue
        if semantic is None:
            counts["missing_semantic_score"] += 1
            by_family[family]["missing_semantic_score"] += 1
            output.append(row)
            continue
        score = semantic * (donor_p**lam)
        verification = verification_by_id.get(row["prediction_id"])
        status = h001_eval.verification_status(verification)
        counts[f"scored_original_status_{status}"] += 1
        by_family[family][f"scored_original_status_{status}"] += 1
        counts["scored_predictions"] += 1
        by_family[family]["scored_predictions"] += 1
        donor_values.append(donor_p)
        scores.append(score)
        output.append(
            h001_eval.copy_with_ranking_score(
                row,
                score,
                f"semantic_ranking_score*{control_name}_p_geom_valid^lambda",
                extra_scores={
                    donor_field: donor_p,
                    "h001_v2_lambda_star": lam,
                    "lambda_control": control_name,
                },
            )
        )

    if counts.get("missing_control_p_geom_valid"):
        errors.append(f"{control_name}:missing_control_p_geom_valid:{counts['missing_control_p_geom_valid']}")
    if counts.get("missing_semantic_score"):
        errors.append(f"{control_name}:missing_semantic_score:{counts['missing_semantic_score']}")
    summary = {
        "policy": f"control_{control_name}",
        "selection_rule": (
            "score = semantic_score * corrupted_or_control_p_geom_valid^lambda_star; "
            "violation is measured against original geometry"
        ),
        "lambda_star": lam,
        "score_formula": f"semantic_ranking_score*{control_name}_p_geom_valid^lambda",
        "control_name": control_name,
        "donor_field": donor_field,
        "shuffle_policy": shuffle_policy,
        "counts": dict(sorted(counts.items())),
        "by_family": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(by_family.items())
        },
        "control_p_geom_valid": h001_eval.summarize_values(donor_values),
        "lambda_control_score": h001_eval.summarize_values(scores),
    }
    return output, summary, errors


def selected_predictions_for_max_k(
    predictions: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    max_k: int,
    lam: float,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    grouped = h001_eval.sorted_by_subgraph(predictions)
    for subgraph_id, rows in sorted(grouped.items()):
        for rank, row in enumerate(rows[:max_k], 1):
            verification = verification_by_id.get(row["prediction_id"])
            selected.append(
                {
                    "source_prediction": row,
                    "h001_v2_lambda_selection": {
                        "subgraph_id": subgraph_id,
                        "selection_rank": rank,
                        "max_k": max_k,
                        "lambda_star": lam,
                        "p_geom_valid": h001_eval.p_geom_valid_from_verification(verification),
                        "verification_status": h001_eval.verification_status(verification),
                    },
                }
            )
    return selected


def metric_delta(
    metrics: dict[str, Any],
    lhs_condition: str,
    rhs_condition: str,
    ks: list[int],
) -> dict[str, Any]:
    lhs = metrics["conditions"].get(lhs_condition, {})
    rhs = metrics["conditions"].get(rhs_condition, {})
    result: dict[str, Any] = {"by_k": {}}
    for k in ks:
        key = str(k)
        lhs_recall = lhs.get("recall", {}).get("by_k", {}).get(key, {}).get("recall")
        rhs_recall = rhs.get("recall", {}).get("by_k", {}).get(key, {}).get("recall")
        lhs_v = lhs.get("violation_rate", {}).get("by_k", {}).get(key, {}).get("violation_rate")
        rhs_v = rhs.get("violation_rate", {}).get("by_k", {}).get(key, {}).get("violation_rate")
        result["by_k"][key] = {
            "delta_recall": (
                float(lhs_recall) - float(rhs_recall)
                if lhs_recall is not None and rhs_recall is not None
                else None
            ),
            "delta_violation_rate": (
                float(lhs_v) - float(rhs_v)
                if lhs_v is not None and rhs_v is not None
                else None
            ),
        }
    return result


def condition_table(metrics: dict[str, Any], ks: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition, values in metrics["conditions"].items():
        row: dict[str, Any] = {"condition": condition}
        for k in ks:
            key = str(k)
            row[f"R@{k}"] = values.get("recall", {}).get("by_k", {}).get(key, {}).get("recall")
            row[f"V@{k}"] = (
                values.get("violation_rate", {})
                .get("by_k", {})
                .get(key, {})
                .get("violation_rate")
            )
            row[f"selected@{k}"] = (
                values.get("recall", {})
                .get("by_k", {})
                .get(key, {})
                .get("selected_predictions")
            )
        rows.append(row)
    return rows


def make_report(metrics: dict[str, Any]) -> str:
    lines = [
        "# H001_v2 Lambda-Soft Source Evaluation",
        "",
        f"Created at: `{metrics['created_at']}`",
        f"Source: `{metrics['source_id']}`",
        f"Status: `{metrics['status']}`",
        f"Families: `{', '.join(metrics['families'])}`",
        f"K values: `{', '.join(str(k) for k in metrics['ks'])}`",
        "",
        "## Fixed Lambda Policy",
        "",
        f"- lambda*: `{metrics['policy']['lambda_star']}`",
        f"- objective: `{metrics['policy']['selection_objective']}`",
        f"- score formula: `{metrics['policy']['score_formula']}`",
        "",
        "## Metrics",
        "",
        "| Condition | "
        + " | ".join(f"R@{k} | V@{k} | selected@{k}" for k in metrics["ks"])
        + " |",
        "| --- | " + " | ".join("---:" for _ in range(len(metrics["ks"]) * 3)) + " |",
    ]
    for row in condition_table(metrics, metrics["ks"]):
        cells = [row["condition"]]
        for k in metrics["ks"]:
            recall = row[f"R@{k}"]
            violation = row[f"V@{k}"]
            selected = row[f"selected@{k}"]
            cells.extend(
                [
                    f"{recall:.4f}" if recall is not None else "NA",
                    f"{violation:.4f}" if violation is not None else "NA",
                    str(selected) if selected is not None else "NA",
                ]
            )
        lines.append("| " + " | ".join(cells) + " |")
    h2 = metrics["conditions"]["h001_v2_lambda_soft_reranking"]["score_summary"]
    lines.extend(
        [
            "",
            "## H001_v2 Lambda-Soft Summary",
            "",
            f"- in-scope predictions: `{h2['counts'].get('in_scope_predictions', 0)}`",
            f"- scored predictions: `{h2['counts'].get('scored_predictions', 0)}`",
            f"- missing verification: `{h2['counts'].get('missing_verification', 0)}`",
            f"- missing p_geom_valid: `{h2['counts'].get('missing_p_geom_valid', 0)}`",
            f"- missing semantic score: `{h2['counts'].get('missing_semantic_score', 0)}`",
            "",
            "## Deltas",
            "",
        ]
    )
    for name, delta in metrics["deltas"].items():
        lines.append(f"### {name}")
        for k, item in delta["by_k"].items():
            lines.append(
                f"- K={k}: Delta R `{item['delta_recall']}`, "
                f"Delta V `{item['delta_violation_rate']}`"
            )
        lines.append("")
    if metrics.get("warnings"):
        lines.extend(["## Warnings", ""])
        for warning in metrics["warnings"]:
            lines.append(f"- `{warning}`")
        lines.append("")
    return "\n".join(lines)


def command_markdown(argv: list[str]) -> str:
    return "\n".join(
        [
            "# H001_v2 Lambda Source Evaluation Command",
            "",
            "```bash",
            " ".join(argv),
            "```",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    repo_root = resolve_path(REPO_ROOT, args.repo_root).resolve()
    predictions_path = resolve_path(repo_root, args.predictions_jsonl)
    gt_path = resolve_path(repo_root, args.ground_truth_jsonl)
    verification_path = resolve_path(repo_root, args.verification_jsonl)
    lambda_policy_path = resolve_path(repo_root, args.lambda_policy_json)
    output_dir = resolve_path(repo_root, args.output_dir)

    for name, path in {
        "predictions_jsonl": predictions_path,
        "ground_truth_jsonl": gt_path,
        "verification_jsonl": verification_path,
        "lambda_policy_json": lambda_policy_path,
    }.items():
        if not path.exists():
            raise FileNotFoundError(f"missing_input:{name}:{repo_rel(path, repo_root)}")
    assert_writable_output(repo_root, output_dir, args.overwrite)

    lambda_policy = load_lambda_policy(lambda_policy_path)
    lam = float(lambda_policy["lambda_star"])
    families = set(args.families)
    ks = sorted(args.ks)

    predictions = h001_eval.load_jsonl(predictions_path)
    ground_truth = h001_eval.load_jsonl(gt_path)
    verification_by_id = h001_eval.load_verification(verification_path)

    metrics: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
        "source_id": args.source_id,
        "families": sorted(families),
        "ks": ks,
        "inputs": {
            "predictions_jsonl": repo_rel(predictions_path, repo_root),
            "ground_truth_jsonl": repo_rel(gt_path, repo_root),
            "verification_jsonl": repo_rel(verification_path, repo_root),
            "lambda_policy_json": repo_rel(lambda_policy_path, repo_root),
        },
        "policy": lambda_policy,
        "counts": {
            "predictions": len(predictions),
            "ground_truth": len(ground_truth),
            "verification_rows": len(verification_by_id),
            "predictions_by_family": dict(
                sorted(Counter(row["predicate"]["predicate_family"] for row in predictions).items())
            ),
            "ground_truth_by_family": dict(
                sorted(Counter(row["predicate_family"] for row in ground_truth).items())
            ),
        },
        "conditions": {},
        "deltas": {},
        "warnings": [],
    }

    metrics["conditions"]["semantic_only"] = {
        "recall": h001_eval.recall_at_k(predictions, ground_truth, ks, families),
        "violation_rate": h001_eval.violation_rate_at_k(
            predictions,
            verification_by_id,
            ks,
            families,
        ),
        "selected_count_summary": selected_count_summary(predictions, ks, families),
    }

    recalibrated, recal_summary, recal_errors = h001_eval.recalibrated_predictions(
        predictions,
        verification_by_id,
        families,
    )
    if recal_errors:
        metrics["warnings"].extend(f"probabilistic_recalibrated:{error}" for error in recal_errors)
    metrics["conditions"]["probabilistic_recalibrated"] = {
        "score_summary": recal_summary,
        "recall": h001_eval.recall_at_k(recalibrated, ground_truth, ks, families),
        "violation_rate": h001_eval.violation_rate_at_k(
            recalibrated,
            verification_by_id,
            ks,
            families,
        ),
        "selected_count_summary": selected_count_summary(recalibrated, ks, families),
    }

    lambda_predictions, lambda_summary, lambda_errors = lambda_soft_predictions(
        predictions,
        verification_by_id,
        families,
        lam,
    )
    if lambda_errors:
        metrics["warnings"].extend(f"h001_v2_lambda_soft_reranking:{error}" for error in lambda_errors)
    lambda_selected = selected_predictions_for_max_k(
        lambda_predictions,
        verification_by_id,
        max(ks),
        lam,
    )
    metrics["conditions"]["h001_v2_lambda_soft_reranking"] = {
        "score_summary": lambda_summary,
        "selected_count_summary": selected_count_summary(lambda_predictions, ks, families),
        "recall": h001_eval.recall_at_k(lambda_predictions, ground_truth, ks, families),
        "violation_rate": h001_eval.violation_rate_at_k(
            lambda_predictions,
            verification_by_id,
            ks,
            families,
        ),
    }

    control_summaries: dict[str, Any] = {}
    for control_name in ("shuffled_geometry_lambda", "wrong_pair_geometry_lambda"):
        condition_name = f"control_{control_name}"
        control_predictions, control_summary, control_errors = lambda_control_predictions(
            predictions,
            verification_by_id,
            families,
            lam,
            control_name,
        )
        if control_errors:
            metrics["warnings"].extend(f"{condition_name}:{error}" for error in control_errors)
        control_summaries[condition_name] = control_summary
        metrics["conditions"][condition_name] = {
            "score_summary": control_summary,
            "selected_count_summary": selected_count_summary(control_predictions, ks, families),
            "recall": h001_eval.recall_at_k(control_predictions, ground_truth, ks, families),
            "violation_rate": h001_eval.violation_rate_at_k(
                control_predictions,
                verification_by_id,
                ks,
                families,
            ),
        }

    metrics["deltas"]["lambda_soft_minus_semantic_only"] = metric_delta(
        metrics,
        "h001_v2_lambda_soft_reranking",
        "semantic_only",
        ks,
    )
    metrics["deltas"]["lambda_soft_minus_probabilistic_recalibrated"] = metric_delta(
        metrics,
        "h001_v2_lambda_soft_reranking",
        "probabilistic_recalibrated",
        ks,
    )
    metrics["deltas"]["lambda_soft_minus_control_shuffled_geometry_lambda"] = metric_delta(
        metrics,
        "h001_v2_lambda_soft_reranking",
        "control_shuffled_geometry_lambda",
        ks,
    )
    metrics["deltas"]["lambda_soft_minus_control_wrong_pair_geometry_lambda"] = metric_delta(
        metrics,
        "h001_v2_lambda_soft_reranking",
        "control_wrong_pair_geometry_lambda",
        ks,
    )

    selection_summary = {
        "schema_version": "h001_v2_lambda_selection_summary_v1",
        "source_id": args.source_id,
        "policy": lambda_policy,
        "h001_v2_lambda_summary": lambda_summary,
        "control_summaries": control_summaries,
        "selected_count_summary": selected_count_summary(lambda_predictions, ks, families),
        "status_counts_all_in_scope": status_counts_for(
            in_scope_predictions(predictions, families),
            verification_by_id,
        ),
        "status_counts_selected_max_k": status_counts_for(
            [row["source_prediction"] for row in lambda_selected],
            verification_by_id,
        ),
    }
    manifest = {
        "schema_version": "h001_v2_lambda_source_eval_manifest_v1",
        "created_at": metrics["created_at"],
        "status": metrics["status"],
        "source_id": args.source_id,
        "code": "src/geocalib/evaluate_h001_v2_lambda_source.py",
        "inputs": metrics["inputs"],
        "outputs": {
            "metrics_json": "metrics.json",
            "report_md": "report.md",
            "selected_predictions_jsonl": "selected_predictions.jsonl",
            "selection_summary_json": "selection_summary.json",
            "commands_md": "commands.md",
        },
        "policy": lambda_policy,
        "notes": [
            "Lambda is selected from calibration dev rows only.",
            "The lambda-soft score is applied to source predictions without source-metric tuning.",
            "Lambda controls apply the same lambda to deterministic corrupted/control geometry scores.",
            "Existing H001 source metrics and paper files are read-only.",
        ],
    }

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "selection_summary.json", selection_summary)
    write_jsonl(output_dir / "selected_predictions.jsonl", lambda_selected)
    (output_dir / "report.md").write_text(make_report(metrics), encoding="utf-8")
    (output_dir / "commands.md").write_text(command_markdown(sys.argv), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": metrics["status"],
                "source_id": args.source_id,
                "lambda_star": lam,
                "output_dir": repo_rel(output_dir, repo_root),
                "scored": lambda_summary["counts"].get("scored_predictions", 0),
                "selected_max_k": len(lambda_selected),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
