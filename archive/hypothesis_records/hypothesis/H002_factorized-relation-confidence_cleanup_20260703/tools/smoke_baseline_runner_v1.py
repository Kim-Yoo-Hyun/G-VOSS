#!/usr/bin/env python3
"""Run the first H002 smoke baselines on prototype_dataset_v1.

This runner is diagnostic-only. It does not train a paper model and does not use
validation/test data.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H002_ROOT.parents[2]
DEFAULT_INPUT_ROOT = H002_ROOT / "artifacts/prototype_dataset_v1"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/smoke_baseline_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def safe_float(value: Any, default: float = 0.5) -> float:
    if value is None or value == "":
        return default
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(output) or math.isinf(output):
        return default
    return output


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def rank_inverse(row: dict[str, Any]) -> float:
    rank = safe_float(row.get("Z_e", {}).get("source_rank"), 999.0)
    return 1.0 / (1.0 + max(rank, 0.0))


def source_score(row: dict[str, Any]) -> float:
    return safe_float(row.get("Z_e", {}).get("source_score_normalized"), 0.5)


def p_geom_valid(row: dict[str, Any]) -> float:
    return safe_float(row.get("p_geom_valid_baseline"), 0.5)


def semantic_x_geom(row: dict[str, Any]) -> float:
    score = row.get("model_views", {}).get("semantic_x_geometry_rule", {}).get("score")
    if score is not None:
        return safe_float(score)
    return source_score(row) * p_geom_valid(row)


def generic_geometry_proxy(row: dict[str, Any]) -> float:
    features = row.get("G_e", {}).get("geometry_features", {})
    candidates = [
        safe_float(features.get("support_gap_closeness"), 0.5),
        safe_float(features.get("support_distance_closeness"), 0.5),
        safe_float(features.get("support_xy_overlap_max"), 0.5),
        safe_float(features.get("vertical_margin_abs"), 0.5),
        safe_float(features.get("vertical_interval_overlap"), 0.5),
    ]
    return clamp(sum(candidates) / len(candidates))


def relation_conditioned_geometry_proxy(row: dict[str, Any]) -> float:
    features = row.get("G_e", {}).get("geometry_features", {})
    if "strong_raw_witness_score" in features:
        return clamp(safe_float(features.get("strong_raw_witness_score"), 0.5))
    return generic_geometry_proxy(row)


def q_observability_score(row: dict[str, Any]) -> float:
    q = row.get("Q_e", {})
    score = 0.5
    if q.get("missing_geometry_flag") is False:
        score += 0.25
    if q.get("low_coverage_flag") is False:
        score += 0.15
    if q.get("same_frame_visible") is True:
        score += 0.15
    if q.get("mesh_available") is True:
        score += 0.10
    if safe_float(q.get("multi_view_count"), 0.0) >= 2:
        score += 0.10
    if q.get("unsupported_family_flag") is True:
        score -= 0.30
    if q.get("evidence_conflict_flag") is True:
        score -= 0.20
    return clamp(score)


def concat_proxy(row: dict[str, Any]) -> float:
    return clamp(mean([source_score(row), p_geom_valid(row), generic_geometry_proxy(row), relation_conditioned_geometry_proxy(row)]))


def full_factorized_proxy(row: dict[str, Any]) -> float:
    rel = 0.50 * source_score(row) + 0.50 * relation_conditioned_geometry_proxy(row)
    obs = q_observability_score(row)
    return clamp(obs * rel + (1.0 - obs) * 0.5)


def full_factorized_multiclass(row: dict[str, Any]) -> str:
    obs = q_observability_score(row)
    if obs < 0.55:
        return "abstain"
    return "accept" if full_factorized_proxy(row) >= 0.5 else "reject"


def labels_binary(rows: list[dict[str, Any]], label_fn: Callable[[dict[str, Any]], int]) -> list[int]:
    return [int(label_fn(row)) for row in rows]


def average_ranks(scores: list[float]) -> list[float]:
    indexed = sorted(enumerate(scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    pos = 0
    while pos < len(indexed):
        end = pos + 1
        while end < len(indexed) and indexed[end][1] == indexed[pos][1]:
            end += 1
        avg_rank = (pos + 1 + end) / 2.0
        for idx in range(pos, end):
            ranks[indexed[idx][0]] = avg_rank
        pos = end
    return ranks


def auroc(y: list[int], scores: list[float]) -> float | None:
    positives = sum(y)
    negatives = len(y) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = average_ranks(scores)
    rank_sum_pos = sum(rank for rank, label in zip(ranks, y) if label == 1)
    return (rank_sum_pos - positives * (positives + 1) / 2.0) / (positives * negatives)


def auprc(y: list[int], scores: list[float]) -> float | None:
    positives = sum(y)
    if positives == 0:
        return None
    pairs = sorted(zip(scores, y), key=lambda item: item[0], reverse=True)
    tp = 0
    fp = 0
    prev_recall = 0.0
    ap = 0.0
    for _, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        ap += (recall - prev_recall) * precision
        prev_recall = recall
    return ap


def binary_confusion(y: list[int], scores: list[float], threshold: float = 0.5) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for label, score in zip(y, scores):
        pred = 1 if score >= threshold else 0
        if label == 1 and pred == 1:
            tp += 1
        elif label == 0 and pred == 1:
            fp += 1
        elif label == 0 and pred == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def binary_f1_from_confusion(conf: dict[str, int]) -> float:
    tp = conf["tp"]
    fp = conf["fp"]
    fn = conf["fn"]
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def brier(y: list[int], scores: list[float]) -> float:
    return sum((score - label) ** 2 for label, score in zip(y, scores)) / max(len(y), 1)


def binary_metrics(y: list[int], scores: list[float]) -> dict[str, Any]:
    conf = binary_confusion(y, scores)
    return {
        "n": len(y),
        "positive": sum(y),
        "negative": len(y) - sum(y),
        "auroc": auroc(y, scores),
        "auprc": auprc(y, scores),
        "accuracy_at_0_5": (conf["tp"] + conf["tn"]) / max(len(y), 1),
        "f1_at_0_5": binary_f1_from_confusion(conf),
        "brier": brier(y, scores),
        "confusion_at_0_5": conf,
    }


def class_f1(labels: list[str], preds: list[str], klass: str) -> float:
    tp = sum(1 for label, pred in zip(labels, preds) if label == klass and pred == klass)
    fp = sum(1 for label, pred in zip(labels, preds) if label != klass and pred == klass)
    fn = sum(1 for label, pred in zip(labels, preds) if label == klass and pred != klass)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def multiclass_metrics(labels: list[str], preds: list[str]) -> dict[str, Any]:
    classes = sorted(set(labels) | set(preds))
    f1_by_class = {klass: class_f1(labels, preds, klass) for klass in classes}
    accuracy = sum(1 for label, pred in zip(labels, preds) if label == pred) / max(len(labels), 1)
    return {
        "n": len(labels),
        "classes": classes,
        "label_counts": dict(sorted(Counter(labels).items())),
        "pred_counts": dict(sorted(Counter(preds).items())),
        "accuracy": accuracy,
        "macro_f1": sum(f1_by_class.values()) / max(len(f1_by_class), 1),
        "f1_by_class": f1_by_class,
    }


def prevalence_scores(rows: list[dict[str, Any]], y: list[int], key_fn: Callable[[dict[str, Any]], str]) -> list[float]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row, label in zip(rows, y):
        grouped[key_fn(row)].append(label)
    prevalence = {key: sum(vals) / max(len(vals), 1) for key, vals in grouped.items()}
    fallback = sum(y) / max(len(y), 1)
    return [prevalence.get(key_fn(row), fallback) for row in rows]


def mean_score_by_group(rows: list[dict[str, Any]], scores: list[float], key_fn: Callable[[dict[str, Any]], str]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row, score in zip(rows, scores):
        grouped[key_fn(row)].append(score)
    return {
        key: {"n": len(vals), "mean": mean(vals), "median": median(vals)}
        for key, vals in sorted(grouped.items())
    }


def task_a_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = {"positive", "counterfactual_negative"}
    return [row for row in rows if row.get("counterfactual_axis", {}).get("compatibility_label") in allowed]


def task_c_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("reliability_eval_axis", {}).get("binary_usable")
        and row.get("reliability_eval_axis", {}).get("reliability_label") in {"accept", "reject"}
    ]


def score_map(row: dict[str, Any]) -> dict[str, float]:
    return {
        "B0_constant_0_5": 0.5,
        "B1_source_score": source_score(row),
        "B1_rank_inverse": rank_inverse(row),
        "B3_p_geom_valid": p_geom_valid(row),
        "B4_semantic_x_p_geom_valid": semantic_x_geom(row),
        "B5_generic_geometry_proxy": generic_geometry_proxy(row),
        "B6_relation_conditioned_geometry_proxy": relation_conditioned_geometry_proxy(row),
        "B7_concat_proxy": concat_proxy(row),
        "B8_no_Q_factorized_proxy": 0.50 * source_score(row) + 0.50 * relation_conditioned_geometry_proxy(row),
        "B9_full_two_head_proxy": full_factorized_proxy(row),
    }


def evaluate_binary_task(rows: list[dict[str, Any]], y: list[int]) -> dict[str, Any]:
    scores_by_name: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for name, score in score_map(row).items():
            scores_by_name[name].append(score)
    output = {name: binary_metrics(y, scores) for name, scores in sorted(scores_by_name.items())}
    shortcut_scores = {
        "S_family_prevalence_probe": prevalence_scores(rows, y, lambda row: str(row["T_e"]["relation_family"])),
        "S_predicate_prevalence_probe": prevalence_scores(rows, y, lambda row: str(row["T_e"]["predicate_label"])),
        "S_rank_band_prevalence_probe": prevalence_scores(rows, y, lambda row: str(row["Z_e"]["source_rank_band"])),
        "S_source_id_prevalence_probe": prevalence_scores(rows, y, lambda row: str(row["Z_e"]["source_id"])),
        "S_geometry_feature_count_probe": prevalence_scores(rows, y, lambda row: str(len(row["G_e"]["geometry_features"]))),
    }
    for name, scores in shortcut_scores.items():
        output[name] = binary_metrics(y, scores)
    return output


def task_a_score_drops(rows: list[dict[str, Any]], groups: list[dict[str, Any]]) -> dict[str, Any]:
    row_by_id = {row["row_id"]: row for row in rows}
    score_names = sorted(score_map(rows[0]).keys()) if rows else []
    drops: dict[str, list[float]] = {name: [] for name in score_names}
    pair_rows: list[dict[str, Any]] = []
    for group in groups:
        anchor = row_by_id.get(group.get("anchor_row_id"))
        if not anchor:
            continue
        for cf_id in group.get("counterfactual_row_ids", []):
            counter = row_by_id.get(cf_id)
            if not counter:
                continue
            anchor_scores = score_map(anchor)
            counter_scores = score_map(counter)
            pair_record = {
                "group_id": group["group_id"],
                "anchor_row_id": anchor["row_id"],
                "counterfactual_row_id": counter["row_id"],
                "family": anchor["T_e"]["relation_family"],
                "predicate": anchor["T_e"]["predicate_label"],
            }
            for name in score_names:
                delta = anchor_scores[name] - counter_scores[name]
                drops[name].append(delta)
                pair_record[name] = delta
            pair_rows.append(pair_record)
    summary = {}
    for name, values in drops.items():
        if values:
            summary[name] = {
                "n": len(values),
                "mean_drop": mean(values),
                "median_drop": median(values),
                "positive_drop_fraction": sum(1 for value in values if value > 0) / len(values),
            }
        else:
            summary[name] = {"n": 0, "mean_drop": None, "median_drop": None, "positive_drop_fraction": None}
    return {"summary": summary, "pairs": pair_rows}


def task_b_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [row["observability_axis"]["observability_label"] for row in rows]
    p_obs_scores = [q_observability_score(row) for row in rows]
    binary_labels = [1 if label == "observable" else 0 for label in labels]
    pred_binary = ["observable" if score >= 0.55 else "limited" for score in p_obs_scores]
    majority_label = Counter(labels).most_common(1)[0][0] if labels else "limited"
    return {
        "binary_observable_vs_not": binary_metrics(binary_labels, p_obs_scores),
        "full_p_obs_proxy": multiclass_metrics(labels, pred_binary),
        "majority_label": majority_label,
        "majority": multiclass_metrics(labels, [majority_label for _ in labels]),
        "score_by_family": mean_score_by_group(rows, p_obs_scores, lambda row: str(row["T_e"]["relation_family"])),
    }


def task_c_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    binary_rows = task_c_rows(rows)
    y = [1 if row["reliability_eval_axis"]["reliability_label"] == "accept" else 0 for row in binary_rows]
    binary = evaluate_binary_task(binary_rows, y) if binary_rows else {}
    multi_rows = [
        row
        for row in rows
        if row.get("reliability_eval_axis", {}).get("multiclass_usable")
        and row.get("reliability_eval_axis", {}).get("reliability_label") in {"accept", "reject", "abstain"}
    ]
    labels = [row["reliability_eval_axis"]["reliability_label"] for row in multi_rows]
    preds = [full_factorized_multiclass(row) for row in multi_rows]
    majority_label = Counter(labels).most_common(1)[0][0] if labels else "reject"
    return {
        "binary_accept_vs_reject": binary,
        "multiclass_full_two_head_proxy": multiclass_metrics(labels, preds),
        "multiclass_majority": multiclass_metrics(labels, [majority_label for _ in labels]),
        "majority_label": majority_label,
    }


def family_task_a_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output = {}
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in task_a_rows(rows):
        by_family[str(row["T_e"]["relation_family"])].append(row)
    for family, family_rows in sorted(by_family.items()):
        y = [1 if row["counterfactual_axis"]["compatibility_label"] == "positive" else 0 for row in family_rows]
        output[family] = evaluate_binary_task(family_rows, y)
    return output


def error_cases(rows: list[dict[str, Any]], max_cases: int = 20) -> list[dict[str, Any]]:
    cases = []
    for row in rows:
        label = row.get("reliability_eval_axis", {}).get("reliability_label")
        if label not in {"accept", "reject"}:
            continue
        y = 1 if label == "accept" else 0
        score = full_factorized_proxy(row)
        pred = 1 if score >= 0.5 else 0
        if pred == y:
            continue
        cases.append(
            {
                "row_id": row["row_id"],
                "candidate_relation_text": row["candidate_relation_text"],
                "family": row["T_e"]["relation_family"],
                "predicate": row["T_e"]["predicate_label"],
                "label": label,
                "predicted": "accept" if pred == 1 else "reject",
                "score": score,
                "source_score": source_score(row),
                "p_geom_valid": p_geom_valid(row),
                "relation_conditioned_geometry_proxy": relation_conditioned_geometry_proxy(row),
                "p_obs_proxy": q_observability_score(row),
                "observability_label": row["observability_axis"]["observability_label"],
                "relation_source": row["relation_source"],
            }
        )
    return sorted(cases, key=lambda item: abs(item["score"] - 0.5), reverse=True)[:max_cases]


def validate_inputs(input_root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    validation_errors_path = input_root / "validation_errors.jsonl"
    if not validation_errors_path.exists():
        errors.append({"error_type": "missing_materialization_validation_errors_file"})
    elif validation_errors_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "materialization_validation_errors_nonempty"})
    for idx, row in enumerate(rows, start=1):
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_number": idx, "row_id": row.get("row_id")})
        if "Z_e" in row.get("model_views", {}).get("compatibility_main", {}):
            errors.append({"error_type": "Z_e_in_compatibility_main", "row_id": row.get("row_id")})
    return errors


def gate_summary(metrics_by_task: dict[str, Any], drops: dict[str, Any], validation_errors: list[dict[str, Any]]) -> dict[str, Any]:
    task_a = metrics_by_task["task_a_compatibility"]
    source_auc = task_a.get("B1_source_score", {}).get("auroc")
    compat_auc = task_a.get("B6_relation_conditioned_geometry_proxy", {}).get("auroc")
    sxg_auc = task_a.get("B4_semantic_x_p_geom_valid", {}).get("auroc")
    family_auc = task_a.get("S_family_prevalence_probe", {}).get("auroc")
    compat_drop = drops["summary"].get("B6_relation_conditioned_geometry_proxy", {})
    obs = metrics_by_task["task_b_observability"]["full_p_obs_proxy"]
    full_multi = metrics_by_task["task_c_reliability"]["multiclass_full_two_head_proxy"]
    gates = {
        "gate_1_dataset_sanity": {
            "pass": not validation_errors and task_a.get("B0_constant_0_5", {}).get("positive") == task_a.get("B0_constant_0_5", {}).get("negative"),
            "notes": "Requires zero materialization errors and balanced Task A positives/negatives.",
        },
        "gate_2_compatibility_signal": {
            "pass": (
                compat_auc is not None
                and source_auc is not None
                and compat_auc > source_auc
                and compat_drop.get("mean_drop", 0.0) > 0.0
            ),
            "source_auc": source_auc,
            "compatibility_proxy_auc": compat_auc,
            "semantic_x_geometry_auc": sxg_auc,
            "family_probe_auc": family_auc,
            "compatibility_mean_drop": compat_drop.get("mean_drop"),
            "notes": "This is a deterministic proxy gate, not learned C_e performance.",
        },
        "gate_3_observability_signal": {
            "pass": obs.get("macro_f1", 0.0) > metrics_by_task["task_b_observability"]["majority"].get("macro_f1", 1.0),
            "p_obs_macro_f1": obs.get("macro_f1"),
            "majority_macro_f1": metrics_by_task["task_b_observability"]["majority"].get("macro_f1"),
        },
        "gate_4_factorized_benefit": {
            "pass": full_multi.get("macro_f1", 0.0) > metrics_by_task["task_c_reliability"]["multiclass_majority"].get("macro_f1", 1.0),
            "full_macro_f1": full_multi.get("macro_f1"),
            "majority_macro_f1": metrics_by_task["task_c_reliability"]["multiclass_majority"].get("macro_f1"),
            "notes": "Gate 4 is conservative; this runner uses deterministic proxies rather than trained heads.",
        },
    }
    gates["overall_interpretation"] = (
        "ready_for_learned_smoke"
        if gates["gate_1_dataset_sanity"]["pass"] and gates["gate_2_compatibility_signal"]["pass"]
        else "diagnostic_only_needs_runner_or_feature_repair"
    )
    return gates


def write_report(path: Path, summary: dict[str, Any], gates: dict[str, Any], metrics_by_task: dict[str, Any]) -> None:
    task_a = metrics_by_task["task_a_compatibility"]
    lines = [
        "# H002 Smoke Baseline V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Dataset",
        "",
        f"- rows: `{summary['counts']['prototype_rows']}`",
        f"- task A compatibility rows: `{summary['counts']['task_a_rows']}`",
        f"- task C binary rows: `{summary['counts']['task_c_binary_rows']}`",
        f"- validation errors: `{summary['counts']['validation_errors']}`",
        "",
        "## Key Task A Metrics",
        "",
        "| Condition | AUROC | AUPRC |",
        "| --- | ---: | ---: |",
    ]
    for name in [
        "B1_source_score",
        "B3_p_geom_valid",
        "B4_semantic_x_p_geom_valid",
        "B5_generic_geometry_proxy",
        "B6_relation_conditioned_geometry_proxy",
        "B7_concat_proxy",
        "S_family_prevalence_probe",
        "S_predicate_prevalence_probe",
    ]:
        metric = task_a.get(name, {})
        auc = metric.get("auroc")
        ap = metric.get("auprc")
        lines.append(f"| `{name}` | {auc if auc is not None else 'null'} | {ap if ap is not None else 'null'} |")
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- gate 1 dataset sanity: `{gates['gate_1_dataset_sanity']['pass']}`",
            f"- gate 2 compatibility signal: `{gates['gate_2_compatibility_signal']['pass']}`",
            f"- gate 3 observability signal: `{gates['gate_3_observability_signal']['pass']}`",
            f"- gate 4 factorized benefit: `{gates['gate_4_factorized_benefit']['pass']}`",
            f"- overall: `{gates['overall_interpretation']}`",
            "",
            "## Boundary",
            "",
            "- train-only diagnostic smoke",
            "- no validation/test usage",
            "- no paper-level evidence",
            "- deterministic proxy baselines only; no learned C_e/p_obs/p_rel yet",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_root = args.input_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(input_root / "prototype_rows.jsonl")
    groups = read_jsonl(input_root / "counterfactual_groups.jsonl")
    materialization_summary = read_json(input_root / "summary.json")
    validation_errors = validate_inputs(input_root, rows)

    task_a = task_a_rows(rows)
    task_a_y = [1 if row["counterfactual_axis"]["compatibility_label"] == "positive" else 0 for row in task_a]
    task_a_metrics = evaluate_binary_task(task_a, task_a_y) if task_a else {}
    drops = task_a_score_drops(rows, groups)
    metrics_by_task = {
        "task_a_compatibility": task_a_metrics,
        "task_b_observability": task_b_metrics(rows),
        "task_c_reliability": task_c_metrics(rows),
    }
    family_metrics = {"task_a_by_family": family_task_a_metrics(rows)}
    gates = gate_summary(metrics_by_task, drops, validation_errors)
    cases = error_cases(rows)
    summary = {
        "schema_version": "h002_smoke_baseline_v1_summary",
        "status": "h002_smoke_baseline_v1_completed" if not validation_errors else "h002_smoke_baseline_v1_input_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_root": rel_path(input_root),
        "output_dir": rel_path(output_dir),
        "materialization_status": materialization_summary.get("status"),
        "counts": {
            "prototype_rows": len(rows),
            "counterfactual_groups": len(groups),
            "task_a_rows": len(task_a),
            "task_a_positive": sum(task_a_y),
            "task_a_negative": len(task_a_y) - sum(task_a_y),
            "task_c_binary_rows": len(task_c_rows(rows)),
            "validation_errors": len(validation_errors),
        },
        "gates": gates,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_model": False,
            "paper_evidence_allowed": False,
            "deterministic_proxy_only": True,
        },
        "interpretation": {
            "task_a_scope": "support_contact and relative_vertical numeric G_e subset",
            "attachment_scope": "reliability/observability diagnostic only",
            "learned_model_status": "not_trained",
        },
        "next_todo": (
            "learned_smoke_runner_v1"
            if gates["gate_1_dataset_sanity"]["pass"] and gates["gate_2_compatibility_signal"]["pass"]
            else "smoke_baseline_v1_error_analysis"
        ),
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "metrics_by_task.json", metrics_by_task)
    write_json(output_dir / "metrics_by_family.json", family_metrics)
    write_json(output_dir / "counterfactual_score_drop.json", drops["summary"])
    write_jsonl(output_dir / "counterfactual_pair_drops.jsonl", drops["pairs"])
    shortcut_metrics = {
        name: value
        for name, value in task_a_metrics.items()
        if name.startswith("S_")
    }
    write_json(output_dir / "shortcut_probe_metrics.json", shortcut_metrics)
    ablation_metrics = {
        name: value
        for name, value in task_a_metrics.items()
        if name.startswith("B")
    }
    write_json(output_dir / "ablation_metrics.json", ablation_metrics)
    write_jsonl(output_dir / "error_cases.jsonl", cases)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_report(output_dir / "report.md", summary, gates, metrics_by_task)
    return summary


def main() -> int:
    summary = run(parse_args())
    gate2 = summary["gates"]["gate_2_compatibility_signal"]
    print(
        "status={status} rows={rows} task_a={task_a} gate1={gate1} gate2={gate2_pass} "
        "source_auc={source_auc} compat_auc={compat_auc} validation_errors={errors} next={next_todo}".format(
            status=summary["status"],
            rows=summary["counts"]["prototype_rows"],
            task_a=summary["counts"]["task_a_rows"],
            gate1=summary["gates"]["gate_1_dataset_sanity"]["pass"],
            gate2_pass=gate2["pass"],
            source_auc=gate2["source_auc"],
            compat_auc=gate2["compatibility_proxy_auc"],
            errors=summary["counts"]["validation_errors"],
            next_todo=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
