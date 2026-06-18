#!/usr/bin/env python3
"""Audit label-policy recoverability in full-train H002 bootstrap labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke
import full_train_controlled_posterior_smoke as posterior


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_INPUT_ROWS = RGA_ROOT / "controlled_posterior_smoke_codex_ver/full_train_controlled_codex_ver_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "label_policy_audit_codex_ver"

GROUP_KEYS = [
    "proposed_audit_role",
    "label_match_status",
    "final_controlled_label",
    "failure_taxonomy_label",
    "queue_kind",
    "geometry_status",
    "candidate_axis",
    "rank_band",
    "predicate_family",
    "predicate_label",
]

MODEL_VIEWS = [
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "residual_reliability_model",
    "negative_rank_only",
    "queue_only",
    "candidate_axis_only",
    "family_only",
    "predicate_only",
    "label_status_only",
    "geometry_status_only",
    "proposed_role_only",
    "p_geom_valid_only",
]

COMPARISON_PAIRS = [
    ("factorized_reliability_posterior", "semantic_plus_geometry"),
    ("residual_reliability_model", "semantic_plus_geometry"),
    ("factorized_reliability_posterior", "negative_rank_only"),
    ("factorized_reliability_posterior", "queue_only"),
    ("factorized_reliability_posterior", "label_status_only"),
    ("factorized_reliability_posterior", "proposed_role_only"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def entropy_from_counts(pos: int, neg: int) -> float:
    total = pos + neg
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in [pos, neg]:
        if count <= 0:
            continue
        prob = count / total
        entropy -= prob * math.log2(prob)
    return entropy


def row_value(row: dict[str, Any], key: str) -> str:
    if key in {"predicate_family", "predicate_label"}:
        return str(row["identity"].get(key))
    return str(row["target"].get(key))


def group_policy_table(rows: list[dict[str, Any]], group_key: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[row_value(row, group_key)].append(row)

    table = []
    weighted_majority_correct = 0
    weighted_entropy = 0.0
    total = len(rows)
    for group, group_rows in sorted(by_group.items()):
        counts = Counter(smoke.target_y(row) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        majority_label = 1 if pos >= neg else 0
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
                "majority_label": majority_label,
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
        "positive": total_counts[1],
        "negative": total_counts[0],
        "overall_entropy_bits": y_entropy,
        "conditional_entropy_bits": weighted_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": mutual_info / y_entropy if y_entropy else 0.0,
        "majority_rule_accuracy": weighted_majority_correct / total if total else 0.0,
        "single_class_groups": sum(1 for row in table if row["positive"] == 0 or row["negative"] == 0),
    }
    return table, summary


def category_prior_scores(rows: list[dict[str, Any]], group_key: str, *, alpha: float = 1.0) -> list[float]:
    if not rows:
        return []
    global_rate = sum(smoke.target_y(row) for row in rows) / len(rows)
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        counts[row_value(row, group_key)][smoke.target_y(row)] += 1
    scores = []
    for row in rows:
        group = row_value(row, group_key)
        y = smoke.target_y(row)
        pos = counts[group][1] - (1 if y == 1 else 0)
        total = counts[group][0] + counts[group][1] - 1
        score = (pos + alpha * global_rate) / (total + alpha) if total > 0 else global_rate
        scores.append(score)
    return scores


def stable_key(row: dict[str, Any]) -> tuple[float, str]:
    rank = smoke.safe_float(row["target"].get("semantic_rank"), 0.0)
    return (rank, str(row["identity"].get("prediction_id")))


def clone_variant(rows: list[dict[str, Any]], target_mode: str, reason: str) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        copied = deepcopy(row)
        copied["target"]["target_mode"] = target_mode
        copied["target"]["variant_reason"] = reason
        output.append(copied)
    return output


def balanced_by_group(rows: list[dict[str, Any]], group_keys: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[tuple(row_value(row, key) for key in group_keys)].append(idx)

    selected: set[int] = set()
    for _, indices in sorted(groups.items()):
        positives = [idx for idx in indices if smoke.target_y(rows[idx]) == 1]
        negatives = [idx for idx in indices if smoke.target_y(rows[idx]) == 0]
        if not positives or not negatives:
            continue
        minority, majority = (positives, negatives) if len(positives) <= len(negatives) else (negatives, positives)
        selected.update(minority)
        used_majority: set[int] = set()
        for idx in sorted(minority, key=lambda row_idx: stable_key(rows[row_idx])):
            rank = stable_key(rows[idx])[0]
            candidates = [row_idx for row_idx in majority if row_idx not in used_majority]
            if not candidates:
                break
            match = min(
                candidates,
                key=lambda row_idx: (
                    abs(stable_key(rows[row_idx])[0] - rank),
                    stable_key(rows[row_idx])[1],
                ),
            )
            used_majority.add(match)
            selected.add(match)
    return [deepcopy(rows[idx]) for idx in sorted(selected, key=lambda row_idx: stable_key(rows[row_idx]))]


def build_variants(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    variants = {
        "original_full_train_codex_ver": clone_variant(
            rows,
            "original_full_train_codex_ver",
            "full-train codex_ver_full_train binary target",
        ),
        "label_status_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["label_match_status"]),
            "label_status_balanced_codex_ver",
            "matched positives/negatives within label_match_status; single-class statuses excluded",
        ),
        "queue_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["queue_kind"]),
            "queue_balanced_codex_ver",
            "matched positives/negatives within HL/LH queue",
        ),
        "geometry_status_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["geometry_status"]),
            "geometry_status_balanced_codex_ver",
            "matched positives/negatives within geometry_status",
        ),
        "family_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["predicate_family"]),
            "family_balanced_codex_ver",
            "matched positives/negatives within predicate_family",
        ),
        "predicate_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["predicate_label"]),
            "predicate_balanced_codex_ver",
            "matched positives/negatives within predicate_label; single-class predicates excluded",
        ),
        "queue_family_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["queue_kind", "predicate_family"]),
            "queue_family_balanced_codex_ver",
            "matched positives/negatives within queue_kind and predicate_family",
        ),
        "proposed_role_balanced_codex_ver": clone_variant(
            balanced_by_group(rows, ["proposed_audit_role"]),
            "proposed_role_balanced_codex_ver",
            "matched positives/negatives within proposed_audit_role; expected to collapse if roles define labels",
        ),
    }
    return variants


def target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(row_value(row, "predicate_family") for row in rows).items())),
        "by_label_status": dict(sorted(Counter(row_value(row, "label_match_status") for row in rows).items())),
        "by_role": dict(sorted(Counter(row_value(row, "proposed_audit_role") for row in rows).items())),
    }


def can_fit(rows: list[dict[str, Any]]) -> bool:
    counts = Counter(smoke.target_y(row) for row in rows)
    return len(rows) >= 8 and counts[0] >= 2 and counts[1] >= 2


def usable_folds(rows: list[dict[str, Any]], requested_folds: int) -> int:
    counts = Counter(smoke.target_y(row) for row in rows)
    return max(2, min(requested_folds, counts[0], counts[1], len(rows)))


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
        local_folds = usable_folds(rows, folds)
        for view_name in MODEL_VIEWS:
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                rows,
                view_name,
                folds=local_folds,
                epochs=epochs,
                learning_rate=learning_rate,
                l2=l2,
            )
            grouped_probs, grouped_summary = posterior.train_predict_grouped(
                rows,
                view_name,
                folds=local_folds,
                epochs=epochs,
                learning_rate=learning_rate,
                l2=l2,
            )
            feature_summaries[f"{target_mode}:{view_name}"] = {
                "crossfit": cross_summary,
                "grouped": grouped_summary,
            }
            metric_rows.append(metric_record("model", target_mode, "train_internal_stratified", view_name, rows, cross_probs))
            metric_rows.append(metric_record("model", target_mode, "train_internal_grouped_by_scan", view_name, rows, grouped_probs))

        for group_key in GROUP_KEYS:
            scores = category_prior_scores(rows, group_key)
            metric_rows.append(metric_record("policy_probe", target_mode, "leave_one_out_probe", f"{group_key}_prior_loo", rows, scores))
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
        for split_eval in ["train_internal_stratified", "train_internal_grouped_by_scan"]:
            for left, right in COMPARISON_PAIRS:
                comparisons.append(comparison(metric_rows, target_mode, split_eval, left, right))
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


def write_comparison_csv(path: Path, comparisons: list[dict[str, Any]]) -> None:
    rows = [
        {
            "target_mode": row["target_mode"],
            "split_eval": row["split_eval"],
            "left": row["left"],
            "right": row["right"],
            "delta_auroc": row["delta"]["auroc"],
            "delta_auprc": row["delta"]["auprc"],
            "delta_brier": row["delta"]["brier"],
        }
        for row in comparisons
    ]
    write_csv(
        path,
        rows,
        ["target_mode", "split_eval", "left", "right", "delta_auroc", "delta_auprc", "delta_brier"],
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Label Policy Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- No validation/test rows are used.",
        "- Labels are `(codex_ver_full_train)` bootstrap labels.",
        "- This audits label-policy recoverability, not paper-level posterior performance.",
        "",
        "## Association Summary",
        "",
        "| Key | Groups | Single-Class Groups | Majority Accuracy | NMI | Conditional Entropy |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["association_summaries"]:
        lines.append(
            f"| `{item['group_key']}` | {item['groups']} | {item['single_class_groups']} | "
            f"{fmt(item['majority_rule_accuracy'])} | {fmt(item['normalized_mutual_information'])} | "
            f"{fmt(item['conditional_entropy_bits'])} |"
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
    selected_views = {
        "semantic_plus_geometry",
        "factorized_reliability_posterior",
        "negative_rank_only",
        "queue_only",
        "label_status_only",
        "proposed_role_only",
    }
    for row in summary["metric_rows"]:
        if row["split_eval"] != "train_internal_grouped_by_scan" or row["kind"] != "model":
            continue
        if row["name"] not in selected_views:
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
            "## Next TODO",
            "",
            summary["next_todo"],
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
    for group_key in GROUP_KEYS:
        table, group_summary = group_policy_table(input_rows, group_key)
        group_tables.extend(table)
        association_summaries.append(group_summary)

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

    summaries = {item["group_key"]: item for item in association_summaries}
    proposed_role = summaries["proposed_audit_role"]
    label_status = summaries["label_match_status"]
    queue = summaries["queue_kind"]
    geometry = summaries["geometry_status"]

    policy_entangled = (
        proposed_role["majority_rule_accuracy"] >= 0.95
        or label_status["majority_rule_accuracy"] >= 0.95
        or proposed_role["normalized_mutual_information"] >= 0.80
    )
    if policy_entangled:
        status = "full_train_label_policy_entangled"
        decision = (
            "The codex_ver_full_train binary target is highly recoverable from label-policy "
            "metadata. Proposed audit role is effectively a target constructor, and "
            "label_match_status is almost sufficient. The full-train result therefore "
            "supports RGA/audit framing, but it does not support a factorized posterior "
            "method claim."
        )
        next_todo = (
            "full_train_independent_label_protocol: create a rank/role-hidden full-train "
            "label protocol before any further posterior revival attempt."
        )
    else:
        status = "full_train_label_policy_risk_not_dominant"
        decision = (
            "The current target is not fully recoverable from label-policy metadata. "
            "A posterior revival smoke may continue, but only with the exported balanced "
            "variants and the same train-only boundary."
        )
        next_todo = (
            "full_train_balanced_posterior_probe: rerun posterior smoke on policy-balanced "
            "variants before escalating any claim."
        )

    summary = {
        "schema_version": "h002_full_train_label_policy_audit_summary_v0",
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
            "label_source": "codex_ver_full_train_policy_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "input_counts": target_counts(input_rows),
        "association_summaries": association_summaries,
        "variant_counts": variant_counts,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "feature_summaries": feature_summaries,
        "quick_findings": {
            "policy_entangled": policy_entangled,
            "proposed_role_majority_accuracy": proposed_role["majority_rule_accuracy"],
            "proposed_role_nmi": proposed_role["normalized_mutual_information"],
            "label_status_majority_accuracy": label_status["majority_rule_accuracy"],
            "label_status_nmi": label_status["normalized_mutual_information"],
            "queue_majority_accuracy": queue["majority_rule_accuracy"],
            "queue_nmi": queue["normalized_mutual_information"],
            "geometry_status_majority_accuracy": geometry["majority_rule_accuracy"],
            "geometry_status_nmi": geometry["normalized_mutual_information"],
        },
        "decision": decision,
        "next_todo": next_todo,
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
    write_comparison_csv(output_dir / "comparisons.csv", comparisons)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    q = summary["quick_findings"]
    print(
        f"status={summary['status']} validation_used={summary['hyperparameters']['uses_validation_rows']} "
        f"rows={summary['input_counts']['rows']} pos={summary['input_counts']['positive']} "
        f"neg={summary['input_counts']['negative']} "
        f"role_majority={q['proposed_role_majority_accuracy']:.4f} role_nmi={q['proposed_role_nmi']:.4f} "
        f"label_status_majority={q['label_status_majority_accuracy']:.4f} "
        f"label_status_nmi={q['label_status_nmi']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
