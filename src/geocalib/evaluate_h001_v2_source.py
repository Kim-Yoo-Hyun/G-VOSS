#!/usr/bin/env python3
"""Evaluate H001_v2 fixed-threshold source metrics under a separate artifact root."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import evaluate_predictions as h001_eval
from paths import REPO_ROOT, repo_rel


SCHEMA_VERSION = "h001_v2_source_eval_v1"
DEFAULT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
DEFAULT_KS = (5, 10, 20, 50, 100)
DEFAULT_THRESHOLDS = (
    Path("hypothesis/CAND-001/H001_v2_risk_controlled_reranking")
    / "artifacts/calibration_threshold_selection/thresholds.json"
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
        description="Evaluate H001_v2 fixed-threshold source metrics."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--predictions-jsonl", type=Path, required=True)
    parser.add_argument("--ground-truth-jsonl", type=Path, required=True)
    parser.add_argument("--verification-jsonl", type=Path, required=True)
    parser.add_argument("--thresholds-json", type=Path, default=DEFAULT_THRESHOLDS)
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
            "Refusing to write H001_v2 source-eval outputs under read-only root: "
            f"{repo_rel(output_dir, repo_root)}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"Output directory is non-empty: {repo_rel(output_dir, repo_root)}. "
                "Pass --overwrite to replace this H001_v2 source-eval output."
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def load_threshold(path: Path) -> dict[str, Any]:
    data = h001_eval.load_json(path)
    if data.get("status") != "ready":
        raise ValueError(f"Threshold policy is not ready: {path}")
    threshold = h001_eval.finite_float(data.get("p_geom_valid_threshold"))
    tau = h001_eval.finite_float(data.get("tau_star"))
    if threshold is None or tau is None:
        raise ValueError(f"Threshold policy lacks tau_star/p_geom_valid_threshold: {path}")
    return data


def in_scope_predictions(predictions: list[dict[str, Any]], families: set[str]) -> list[dict[str, Any]]:
    return [row for row in predictions if h001_eval.in_scope_prediction(row, families)]


def summarize_counts_by_family(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(row["predicate"]["predicate_family"] for row in rows).items()))


def status_counts_for(
    rows: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        status = h001_eval.verification_status(verification_by_id.get(row["prediction_id"]))
        counts[str(status)] += 1
    return dict(sorted(counts.items()))


def h001_v2_predictions(
    predictions: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    families: set[str],
    p_geom_valid_threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output: list[dict[str, Any]] = []
    p_values: list[float] = []
    eligible_p_values: list[float] = []
    counts: Counter[str] = Counter()
    by_family: dict[str, Counter[str]] = defaultdict(Counter)

    for row in predictions:
        family = row["predicate"]["predicate_family"]
        if family not in families:
            counts["family_out_of_scope"] += 1
            continue
        counts["in_scope_predictions"] += 1
        by_family[family]["in_scope_predictions"] += 1
        verification = verification_by_id.get(row["prediction_id"])
        if verification is None:
            counts["missing_verification"] += 1
            by_family[family]["missing_verification"] += 1
            continue
        p_geom_valid = h001_eval.p_geom_valid_from_verification(verification)
        if p_geom_valid is None:
            counts["missing_p_geom_valid"] += 1
            by_family[family]["missing_p_geom_valid"] += 1
            continue
        p_values.append(p_geom_valid)
        semantic_score = h001_eval.semantic_score(row)
        if semantic_score is None:
            counts["missing_semantic_score"] += 1
            by_family[family]["missing_semantic_score"] += 1
            continue
        if p_geom_valid < p_geom_valid_threshold:
            counts["threshold_excluded"] += 1
            by_family[family]["threshold_excluded"] += 1
            continue
        status = h001_eval.verification_status(verification)
        counts[f"eligible_status_{status}"] += 1
        by_family[family][f"eligible_status_{status}"] += 1
        eligible_p_values.append(p_geom_valid)
        output.append(
            h001_eval.copy_with_ranking_score(
                row,
                semantic_score,
                "semantic_ranking_score_after_p_geom_valid_threshold",
                extra_scores={
                    "p_geom_valid": p_geom_valid,
                    "h001_v2_p_geom_valid_threshold": p_geom_valid_threshold,
                },
            )
        )
        counts["eligible_predictions"] += 1
        by_family[family]["eligible_predictions"] += 1

    summary = {
        "policy": "h001_v2_risk_controlled_pooled_tau",
        "selection_rule": "calibration.p_geom_valid >= threshold, then semantic ranking",
        "p_geom_valid_threshold": p_geom_valid_threshold,
        "score_formula": "semantic_ranking_score_after_p_geom_valid_threshold",
        "counts": dict(sorted(counts.items())),
        "by_family": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(by_family.items())
        },
        "p_geom_valid": h001_eval.summarize_values(p_values),
        "eligible_p_geom_valid": h001_eval.summarize_values(eligible_p_values),
    }
    return output, summary


def selected_predictions_for_max_k(
    predictions: list[dict[str, Any]],
    verification_by_id: dict[str, dict[str, Any]],
    max_k: int,
    p_geom_valid_threshold: float,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    grouped = h001_eval.sorted_by_subgraph(predictions)
    for subgraph_id, rows in sorted(grouped.items()):
        for rank, row in enumerate(rows[:max_k], 1):
            verification = verification_by_id.get(row["prediction_id"])
            selected.append(
                {
                    "source_prediction": row,
                    "h001_v2_selection": {
                        "subgraph_id": subgraph_id,
                        "selection_rank": rank,
                        "max_k": max_k,
                        "p_geom_valid_threshold": p_geom_valid_threshold,
                        "p_geom_valid": h001_eval.p_geom_valid_from_verification(verification),
                        "verification_status": h001_eval.verification_status(verification),
                    },
                }
            )
    return selected


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
        "# H001_v2 Source Evaluation",
        "",
        f"Created at: `{metrics['created_at']}`",
        f"Source: `{metrics['source_id']}`",
        f"Status: `{metrics['status']}`",
        f"Families: `{', '.join(metrics['families'])}`",
        f"K values: `{', '.join(str(k) for k in metrics['ks'])}`",
        "",
        "## Fixed Policy",
        "",
        f"- tau*: `{metrics['policy']['tau_star']}`",
        f"- p_geom_valid threshold: `{metrics['policy']['p_geom_valid_threshold']}`",
        f"- alpha/delta: `{metrics['policy']['alpha']}` / `{metrics['policy']['delta']}`",
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
    h2 = metrics["conditions"]["h001_v2_risk_controlled_pooled_tau"]["selection_summary"]
    lines.extend(
        [
            "",
            "## H001_v2 Selection Summary",
            "",
            f"- in-scope predictions: `{h2['counts'].get('in_scope_predictions', 0)}`",
            f"- eligible predictions: `{h2['counts'].get('eligible_predictions', 0)}`",
            f"- threshold-excluded predictions: `{h2['counts'].get('threshold_excluded', 0)}`",
            f"- missing verification: `{h2['counts'].get('missing_verification', 0)}`",
            f"- missing p_geom_valid: `{h2['counts'].get('missing_p_geom_valid', 0)}`",
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
            "# H001_v2 Source Evaluation Command",
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
    thresholds_path = resolve_path(repo_root, args.thresholds_json)
    output_dir = resolve_path(repo_root, args.output_dir)

    for name, path in {
        "predictions_jsonl": predictions_path,
        "ground_truth_jsonl": gt_path,
        "verification_jsonl": verification_path,
        "thresholds_json": thresholds_path,
    }.items():
        if not path.exists():
            raise FileNotFoundError(f"missing_input:{name}:{repo_rel(path, repo_root)}")

    assert_writable_output(repo_root, output_dir, args.overwrite)
    threshold_policy = load_threshold(thresholds_path)
    p_threshold = float(threshold_policy["p_geom_valid_threshold"])
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
            "thresholds_json": repo_rel(thresholds_path, repo_root),
        },
        "policy": threshold_policy,
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

    rule_predictions, rule_summary = h001_eval.apply_rule_filter(
        predictions,
        verification_by_id,
        policy="filter_safe",
        variant="point_subtype",
    )
    metrics["conditions"]["rule_verified_point_subtype"] = {
        "filter": rule_summary,
        "recall": h001_eval.recall_at_k(rule_predictions, ground_truth, ks, families),
        "violation_rate": h001_eval.violation_rate_at_k(
            rule_predictions,
            verification_by_id,
            ks,
            families,
            variant="point_subtype",
        ),
        "selected_count_summary": selected_count_summary(rule_predictions, ks, families),
    }

    h2_predictions, h2_summary = h001_v2_predictions(
        predictions,
        verification_by_id,
        families,
        p_geom_valid_threshold=p_threshold,
    )
    h2_selected = selected_predictions_for_max_k(
        h2_predictions,
        verification_by_id,
        max(ks),
        p_geom_valid_threshold=p_threshold,
    )
    h2_selected_summary = selected_count_summary(h2_predictions, ks, families)
    metrics["conditions"]["h001_v2_risk_controlled_pooled_tau"] = {
        "selection_summary": h2_summary,
        "selected_count_summary": h2_selected_summary,
        "recall": h001_eval.recall_at_k(h2_predictions, ground_truth, ks, families),
        "violation_rate": h001_eval.violation_rate_at_k(
            h2_predictions,
            verification_by_id,
            ks,
            families,
        ),
    }

    metrics["deltas"]["h001_v2_minus_semantic_only"] = metric_delta(
        metrics,
        "h001_v2_risk_controlled_pooled_tau",
        "semantic_only",
        ks,
    )
    metrics["deltas"]["h001_v2_minus_probabilistic_recalibrated"] = metric_delta(
        metrics,
        "h001_v2_risk_controlled_pooled_tau",
        "probabilistic_recalibrated",
        ks,
    )

    selection_summary = {
        "schema_version": "h001_v2_selection_summary_v1",
        "source_id": args.source_id,
        "policy": threshold_policy,
        "h001_v2_selection_summary": h2_summary,
        "selected_count_summary": h2_selected_summary,
        "status_counts_all_in_scope": status_counts_for(
            in_scope_predictions(predictions, families),
            verification_by_id,
        ),
        "status_counts_selected_max_k": status_counts_for(
            [row["source_prediction"] for row in h2_selected],
            verification_by_id,
        ),
    }
    manifest = {
        "schema_version": "h001_v2_source_eval_manifest_v1",
        "created_at": metrics["created_at"],
        "status": metrics["status"],
        "source_id": args.source_id,
        "code": "src/geocalib/evaluate_h001_v2_source.py",
        "inputs": metrics["inputs"],
        "outputs": {
            "metrics_json": "metrics.json",
            "report_md": "report.md",
            "selected_predictions_jsonl": "selected_predictions.jsonl",
            "selection_summary_json": "selection_summary.json",
            "commands_md": "commands.md",
        },
        "policy": threshold_policy,
        "notes": [
            "H001_v2 source metrics use a fixed calibration-selected threshold.",
            "No threshold is selected from source evaluation metrics.",
            "Existing H001 source metrics and paper files are read-only.",
        ],
    }

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "selection_summary.json", selection_summary)
    write_jsonl(output_dir / "selected_predictions.jsonl", h2_selected)
    (output_dir / "report.md").write_text(make_report(metrics), encoding="utf-8")
    (output_dir / "commands.md").write_text(command_markdown(sys.argv), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": metrics["status"],
                "source_id": args.source_id,
                "output_dir": repo_rel(output_dir, repo_root),
                "h001_v2_eligible": h2_summary["counts"].get("eligible_predictions", 0),
                "h001_v2_selected_max_k": len(h2_selected),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
