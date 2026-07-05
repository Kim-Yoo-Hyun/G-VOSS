#!/usr/bin/env python3
"""Audit family/predicate policy bias in H002 independent bootstrap labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
from copy import deepcopy
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import factor_smoke as smoke
import independent_combiner_smoke as combiner


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_INPUT_ROWS = RGA_ROOT / "independent_combiner_smoke_codex_ver/independent_codex_ver_blind_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "label_policy_audit_codex_ver"

AUDIT_VIEWS = [
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "residual_reliability_model",
    "gated_evidence_model",
    "family_only",
    "predicate_only",
    "negative_rank_only",
    "p_geom_valid_only",
]

POLICY_PROBES = [
    "family_prior_loo",
    "predicate_prior_loo",
    "rank_band_prior_loo",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def entropy_from_counts(pos: int, neg: int) -> float:
    total = pos + neg
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in [pos, neg]:
        if count <= 0:
            continue
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def group_value(row: dict[str, Any], key: str) -> str:
    if key == "predicate_family":
        return str(row["identity"]["predicate_family"])
    if key == "predicate_label":
        return str(row["identity"]["predicate_label"])
    if key == "rank_band":
        return str(row["target"].get("rank_band"))
    raise ValueError(f"unsupported group key: {key}")


def group_policy_table(rows: list[dict[str, Any]], group_key: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[group_value(row, group_key)].append(row)

    table = []
    weighted_majority_correct = 0
    weighted_entropy = 0.0
    total = len(rows)
    for group, group_rows in sorted(by_group.items()):
        counts = Counter(smoke.target_y(row) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        majority = 1 if pos >= neg else 0
        majority_correct = max(pos, neg)
        entropy = entropy_from_counts(pos, neg)
        weighted_majority_correct += majority_correct
        weighted_entropy += len(group_rows) / total * entropy
        table.append(
            {
                "group_key": group_key,
                "group_value": group,
                "rows": len(group_rows),
                "positive": pos,
                "negative": neg,
                "positive_rate": pos / len(group_rows),
                "majority_label": majority,
                "majority_accuracy": majority_correct / len(group_rows),
                "entropy_bits": entropy,
            }
        )

    total_counts = Counter(smoke.target_y(row) for row in rows)
    y_entropy = entropy_from_counts(total_counts[1], total_counts[0])
    mutual_info = max(0.0, y_entropy - weighted_entropy)
    summary = {
        "group_key": group_key,
        "groups": len(table),
        "rows": total,
        "overall_positive": total_counts[1],
        "overall_negative": total_counts[0],
        "overall_entropy_bits": y_entropy,
        "conditional_entropy_bits": weighted_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": mutual_info / y_entropy if y_entropy > 0 else 0.0,
        "majority_rule_accuracy": weighted_majority_correct / total if total else 0.0,
    }
    return table, summary


def category_prior_scores(rows: list[dict[str, Any]], group_key: str, *, alpha: float = 1.0) -> list[float]:
    global_pos = sum(smoke.target_y(row) for row in rows)
    global_rate = global_pos / len(rows) if rows else 0.5
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        counts[group_value(row, group_key)][smoke.target_y(row)] += 1
    scores = []
    for row in rows:
        group = group_value(row, group_key)
        y = smoke.target_y(row)
        pos = counts[group][1] - (1 if y == 1 else 0)
        total = counts[group][0] + counts[group][1] - 1
        score = (pos + alpha * global_rate) / (total + alpha) if total > 0 else global_rate
        scores.append(score)
    return scores


def stable_rank(row: dict[str, Any]) -> tuple[float, str]:
    rank = smoke.safe_float(
        row["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"),
        0.0,
    )
    return (rank, str(row["identity"]["prediction_id"]))


def balanced_by_group(rows: list[dict[str, Any]], group_key: str) -> list[dict[str, Any]]:
    selected_indices: set[int] = set()
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[group_value(row, group_key)].append(idx)

    for _, indices in sorted(groups.items()):
        positives = [idx for idx in indices if smoke.target_y(rows[idx]) == 1]
        negatives = [idx for idx in indices if smoke.target_y(rows[idx]) == 0]
        if not positives or not negatives:
            continue
        minority, majority = (positives, negatives) if len(positives) <= len(negatives) else (negatives, positives)
        selected_indices.update(minority)
        used_majority: set[int] = set()
        for idx in sorted(minority, key=lambda row_idx: stable_rank(rows[row_idx])):
            rank = stable_rank(rows[idx])[0]
            candidates = [row_idx for row_idx in majority if row_idx not in used_majority]
            if not candidates:
                break
            match = min(
                candidates,
                key=lambda row_idx: (
                    abs(stable_rank(rows[row_idx])[0] - rank),
                    stable_rank(rows[row_idx])[1],
                ),
            )
            used_majority.add(match)
            selected_indices.add(match)
    return [deepcopy(rows[idx]) for idx in sorted(selected_indices, key=lambda row_idx: stable_rank(rows[row_idx]))]


def clone_variant(rows: list[dict[str, Any]], target_mode: str, variant_reason: str) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        copied = deepcopy(row)
        copied["target"]["target_mode"] = target_mode
        copied["target"]["variant_reason"] = variant_reason
        output.append(copied)
    return output


def build_variants(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    family_balanced = balanced_by_group(rows, "predicate_family")
    predicate_balanced = balanced_by_group(rows, "predicate_label")
    proximity_only = [
        deepcopy(row)
        for row in rows
        if str(row["identity"]["predicate_family"]) == "proximity"
    ]
    return {
        "original_independent_codex_ver_blind": clone_variant(
            rows,
            "original_independent_codex_ver_blind",
            "full independent codex_ver_blind target",
        ),
        "family_balanced_codex_ver_blind": clone_variant(
            family_balanced,
            "family_balanced_codex_ver_blind",
            "matched positives/negatives within predicate_family",
        ),
        "predicate_balanced_codex_ver_blind": clone_variant(
            predicate_balanced,
            "predicate_balanced_codex_ver_blind",
            "matched positives/negatives within predicate_label; single-class predicates excluded",
        ),
        "proximity_only_codex_ver_blind": clone_variant(
            proximity_only,
            "proximity_only_codex_ver_blind",
            "single-family/single-predicate proximity slice",
        ),
    }


def target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    family_counts = Counter((str(row["identity"]["predicate_family"]), smoke.target_y(row)) for row in rows)
    predicate_counts = Counter((str(row["identity"]["predicate_label"]), smoke.target_y(row)) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "predicate_family_y_counts": [
            {"predicate_family": key[0], "y": key[1], "rows": value}
            for key, value in sorted(family_counts.items())
        ],
        "predicate_label_y_counts": [
            {"predicate_label": key[0], "y": key[1], "rows": value}
            for key, value in sorted(predicate_counts.items())
        ],
    }


def can_fit(rows: list[dict[str, Any]]) -> bool:
    return len(rows) >= 8 and {smoke.target_y(row) for row in rows} == {0, 1}


def metric_record(kind: str, target_mode: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": target_mode,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def train_views(
    variants: dict[str, list[dict[str, Any]]],
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metric_rows = []
    feature_summaries: dict[str, Any] = {}
    for target_mode, rows in variants.items():
        if not can_fit(rows):
            continue
        for view_name in AUDIT_VIEWS:
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                rows,
                view_name,
                folds=folds,
                epochs=epochs,
                learning_rate=learning_rate,
                l2=l2,
            )
            grouped_probs, grouped_summary = combiner.train_predict_grouped(
                rows,
                view_name,
                folds=folds,
                epochs=epochs,
                learning_rate=learning_rate,
                l2=l2,
            )
            feature_summaries[f"{target_mode}:{view_name}"] = {
                "crossfit": cross_summary,
                "grouped": grouped_summary,
            }
            metric_rows.append(metric_record("model", target_mode, "train_internal_5fold", view_name, rows, cross_probs))
            metric_rows.append(metric_record("model", target_mode, "train_internal_grouped_by_scan", view_name, rows, grouped_probs))
        probe_defs: list[tuple[str, Callable[[list[dict[str, Any]]], list[float]]]] = [
            ("family_prior_loo", lambda target_rows: category_prior_scores(target_rows, "predicate_family")),
            ("predicate_prior_loo", lambda target_rows: category_prior_scores(target_rows, "predicate_label")),
            ("rank_band_prior_loo", lambda target_rows: category_prior_scores(target_rows, "rank_band")),
        ]
        for probe_name, fn in probe_defs:
            scores = fn(rows)
            metric_rows.append(metric_record("policy_probe", target_mode, "leave_one_out_probe", probe_name, rows, scores))
    return metric_rows, feature_summaries


def comparison(metric_rows: list[dict[str, Any]], target_mode: str, split_eval: str, left: str, right: str) -> dict[str, Any]:
    by_name = {
        row["name"]: row["metrics"]
        for row in metric_rows
        if row["target_mode"] == target_mode and row["split_eval"] == split_eval
    }
    left_metrics = by_name.get(left, {})
    right_metrics = by_name.get(right, {})
    return {
        "target_mode": target_mode,
        "split_eval": split_eval,
        "left": left,
        "right": right,
        "delta": {
            "auroc": (
                left_metrics.get("auroc") - right_metrics.get("auroc")
                if left_metrics.get("auroc") is not None and right_metrics.get("auroc") is not None
                else None
            ),
            "auprc": (
                left_metrics.get("auprc") - right_metrics.get("auprc")
                if left_metrics.get("auprc") is not None and right_metrics.get("auprc") is not None
                else None
            ),
            "brier": (
                left_metrics.get("brier") - right_metrics.get("brier")
                if left_metrics.get("brier") is not None and right_metrics.get("brier") is not None
                else None
            ),
        },
    }


def build_comparisons(metric_rows: list[dict[str, Any]], variants: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    comparisons = []
    for target_mode, rows in variants.items():
        if not can_fit(rows):
            continue
        for split_eval in ["train_internal_5fold", "train_internal_grouped_by_scan"]:
            comparisons.extend(
                [
                    comparison(metric_rows, target_mode, split_eval, "factorized_reliability_posterior", "semantic_plus_geometry"),
                    comparison(metric_rows, target_mode, split_eval, "residual_reliability_model", "semantic_plus_geometry"),
                    comparison(metric_rows, target_mode, split_eval, "gated_evidence_model", "semantic_plus_geometry"),
                    comparison(metric_rows, target_mode, split_eval, "predicate_only", "semantic_plus_geometry"),
                    comparison(metric_rows, target_mode, split_eval, "family_only", "semantic_plus_geometry"),
                ]
            )
    return comparisons


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_metric_csv(path: Path, metric_rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
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
            writer.writerow(
                {
                    "kind": row["kind"],
                    "target_mode": row["target_mode"],
                    "split_eval": row["split_eval"],
                    "name": row["name"],
                    **row["metrics"],
                }
            )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Label Policy Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- No validation/test rows are used.",
        "- Labels are `(codex_ver_blind)` bootstrap labels.",
        "- This audits label-policy bias, not paper-level performance.",
        "",
        "## Association Summary",
        "",
        "| Key | Groups | Majority Accuracy | NMI | Conditional Entropy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["association_summaries"]:
        lines.append(
            f"| `{item['group_key']}` | {item['groups']} | {fmt(item['majority_rule_accuracy'])} | "
            f"{fmt(item['normalized_mutual_information'])} | {fmt(item['conditional_entropy_bits'])} |"
        )
    lines.extend(
        [
            "",
            "## Variant Counts",
            "",
            "| Target | Rows | Positive | Negative |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for target_mode, counts in summary["variant_counts"].items():
        lines.append(f"| `{target_mode}` | {counts['rows']} | {counts['positive']} | {counts['negative']} |")
    lines.extend(
        [
            "",
            "## Grouped Metrics",
            "",
            "| Target | View | AUROC | AUPRC | Brier |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["split_eval"] != "train_internal_grouped_by_scan":
            continue
        if row["kind"] != "model":
            continue
        if row["name"] not in {"semantic_plus_geometry", "factorized_reliability_posterior", "residual_reliability_model", "gated_evidence_model", "family_only", "predicate_only"}:
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | "
            f"{fmt(metrics['auprc'])} | {fmt(metrics['brier'])} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_rows = smoke.read_jsonl(args.input_rows)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    group_tables = []
    association_summaries = []
    for group_key in ["predicate_family", "predicate_label", "rank_band"]:
        table, summary = group_policy_table(input_rows, group_key)
        group_tables.extend(table)
        association_summaries.append(summary)

    variants = build_variants(input_rows)
    variant_counts = {name: target_counts(rows) for name, rows in variants.items()}
    for name, rows in variants.items():
        smoke.write_jsonl(output_dir / f"{name}.jsonl", rows)

    metric_rows, feature_summaries = train_views(
        variants,
        folds=args.folds,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    comparisons = build_comparisons(metric_rows, variants)

    predicate_summary = next(item for item in association_summaries if item["group_key"] == "predicate_label")
    family_summary = next(item for item in association_summaries if item["group_key"] == "predicate_family")
    policy_entangled = (
        predicate_summary["majority_rule_accuracy"] >= 0.70
        or family_summary["majority_rule_accuracy"] >= 0.70
        or predicate_summary["normalized_mutual_information"] >= 0.10
    )
    proximity_delta = next(
        (
            row["delta"]
            for row in comparisons
            if row["target_mode"] == "proximity_only_codex_ver_blind"
            and row["split_eval"] == "train_internal_grouped_by_scan"
            and row["left"] == "gated_evidence_model"
            and row["right"] == "semantic_plus_geometry"
        ),
        None,
    )
    if policy_entangled:
        status = "label_policy_entangled"
        decision = (
            "Current codex_ver_blind labels are strongly entangled with family/predicate "
            "policy. Posterior method claims remain blocked. Use the exported "
            "predicate-balanced and proximity-only variants for the next controlled "
            "target smoke, but treat all results as bootstrap diagnostics."
        )
    elif proximity_delta and proximity_delta.get("auprc") is not None and proximity_delta["auprc"] > 0.03:
        status = "label_policy_risk_with_proximity_signal"
        decision = (
            "Overall family/predicate policy risk is manageable, and proximity-only "
            "has a positive gated/residual signal. Continue with proximity-focused "
            "human confirmation."
        )
    else:
        status = "label_policy_no_clear_combiner_path"
        decision = (
            "Family/predicate policy does not fully explain the target, but no clear "
            "combiner path is established. Keep H002 as RGA benchmark/failure taxonomy "
            "unless stronger labels are collected."
        )

    summary = {
        "schema_version": "h002_label_policy_audit_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "input_rows": smoke.rel_path(args.input_rows),
        },
        "output_dir": smoke.rel_path(output_dir),
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "uses_validation_rows": False,
            "tuned_on_validation": False,
        },
        "boundary": {
            "split": "train_only",
            "label_source": "codex_ver_blind_visible_metadata_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "association_summaries": association_summaries,
        "variant_counts": variant_counts,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "feature_summaries": feature_summaries,
        "quick_findings": {
            "policy_entangled": policy_entangled,
            "predicate_majority_accuracy": predicate_summary["majority_rule_accuracy"],
            "predicate_nmi": predicate_summary["normalized_mutual_information"],
            "family_majority_accuracy": family_summary["majority_rule_accuracy"],
            "family_nmi": family_summary["normalized_mutual_information"],
            "proximity_gated_minus_sg_grouped": proximity_delta,
        },
        "decision": decision,
    }
    smoke.write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)
    write_csv(
        output_dir / "group_policy_table.csv",
        group_tables,
        [
            "group_key",
            "group_value",
            "rows",
            "positive",
            "negative",
            "positive_rate",
            "majority_label",
            "majority_accuracy",
            "entropy_bits",
        ],
    )
    write_metric_csv(output_dir / "metrics.csv", metric_rows)
    comparison_rows = [
        {
            "target_mode": row["target_mode"],
            "split_eval": row["split_eval"],
            "left": row["left"],
            "right": row["right"],
            **{f"delta_{key}": value for key, value in row["delta"].items()},
        }
        for row in comparisons
    ]
    write_csv(
        output_dir / "comparisons.csv",
        comparison_rows,
        ["target_mode", "split_eval", "left", "right", "delta_auroc", "delta_auprc", "delta_brier"],
    )
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    q = summary["quick_findings"]
    proximity = q["proximity_gated_minus_sg_grouped"] or {"auprc": None, "brier": None}
    proximity_auprc = proximity.get("auprc")
    proximity_brier = proximity.get("brier")
    print(
        f"status={summary['status']} validation_used={summary['hyperparameters']['uses_validation_rows']} "
        f"predicate_majority={q['predicate_majority_accuracy']:.4f} predicate_nmi={q['predicate_nmi']:.4f} "
        f"family_majority={q['family_majority_accuracy']:.4f} family_nmi={q['family_nmi']:.4f} "
        f"proximity_gated_d_auprc={proximity_auprc:.4f} proximity_gated_d_brier={proximity_brier:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
