#!/usr/bin/env python3
"""Run p_obs-only diagnostic metric on repaired H002 Q_e v2 views."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_grouped_eval import binary_metrics, fit_model, one_hot, predict_model, safe_float
from run_pobs_prel_selective_metric import ece


SCHEMA_VERSION = "h002_pobs_prel_qe_repair_pobs_only_metric_v1"
STATUS_READY = "h002_pobs_prel_qe_repair_pobs_only_metric_ready"
STATUS_ERROR = "h002_pobs_prel_qe_repair_pobs_only_metric_errors"
EXPECTED_MATERIALIZATION_STATUS = "h002_pobs_prel_qe_repair_materialization_ready"
EXPECTED_SCHEMA_AUDIT_STATUS = "h002_pobs_prel_qe_repair_schema_audit_ready"
TRAIN_SPLIT = "internal_train"
EVAL_SPLIT = "official_validation_diagnostic_subset"
TAU_OBS = 0.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest"),
    )
    parser.add_argument(
        "--schema-audit-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_qe_repair_schema_audit/latest"),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    blocks = row.get("feature_blocks")
    return blocks if isinstance(blocks, dict) else {}


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("Q_e", {})
    return block if isinstance(block, dict) else {}


def flatten_numeric(prefix: str, value: Any) -> dict[str, float]:
    output: dict[str, float] = {}
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            if key == "qe_v2_diagnostic_source":
                continue
            output.update(flatten_numeric(f"{prefix}.{key}", child))
    elif isinstance(value, bool):
        output[prefix] = 1.0 if value else 0.0
    elif isinstance(value, (int, float)):
        output[prefix] = safe_float(value, 0.0)
    return output


def qe_v2_features(row: dict[str, Any]) -> dict[str, float]:
    q = q_block(row)
    out = flatten_numeric("Q", q)
    safe = q.get("Q_e_safe", {}) if isinstance(q.get("Q_e_safe"), dict) else {}
    out.update(one_hot("Q.mesh_or_point_availability", safe.get("mesh_or_point_availability")))
    return out


def qe_state_score(row: dict[str, Any]) -> float:
    state = q_block(row).get("Q_e_state_v2", {})
    if not isinstance(state, dict):
        return 0.5
    return safe_float(state.get("q_e_state_code_v2"), 0.5)


def join_qe_hidden(qe_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    hidden_by_id = {str(row.get("candidate_id")): row for row in hidden_rows if row.get("eval_split") == split}
    rows: list[dict[str, Any]] = []
    for qe in qe_rows:
        candidate_id = str(qe.get("candidate_id"))
        hidden = hidden_by_id.get(candidate_id)
        if hidden is None:
            continue
        row = dict(qe)
        row["obs_label"] = int(hidden["obs_label"])
        row["target_y"] = int(hidden["obs_label"])
        row["observability_label"] = hidden.get("observability_label")
        row["decision_label"] = hidden.get("decision_label")
        row["q_e_state_v2_hidden"] = hidden.get("q_e_state_v2_hidden")
        row["q_e_state_source_hidden"] = hidden.get("q_e_state_source_hidden")
        row["label_provenance"] = hidden.get("label_provenance")
        rows.append(row)
    return rows


def enrich_binary(scope: str, score_id: str, labels: list[int], scores: list[float]) -> dict[str, Any]:
    out = binary_metrics(labels, scores)
    out.update({"scope": scope, "score_id": score_id, "ECE_10": ece(labels, scores)})
    return out


def threshold_metrics(records: list[dict[str, Any]], score_key: str, threshold: float = TAU_OBS) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in records:
        target_abstain = int(row["obs_label"]) == 0
        pred_abstain = float(row[score_key]) < threshold
        if target_abstain and pred_abstain:
            tp += 1
        elif not target_abstain and pred_abstain:
            fp += 1
        elif not target_abstain and not pred_abstain:
            tn += 1
        else:
            fn += 1
    abstain_precision = tp / max(tp + fp, 1)
    abstain_recall = tp / max(tp + fn, 1)
    observable_false_abstain = fp / max(fp + tn, 1)
    false_observable_rate = fn / max(tp + fn, 1)
    accuracy = (tp + tn) / max(tp + fp + tn + fn, 1)
    return {
        "score_id": score_key,
        "threshold": threshold,
        "rows": len(records),
        "abstain_tp": tp,
        "abstain_fp": fp,
        "observable_tn": tn,
        "abstain_fn": fn,
        "abstain_precision": abstain_precision,
        "abstain_recall": abstain_recall,
        "observable_false_abstain_rate": observable_false_abstain,
        "false_observable_rate": false_observable_rate,
        "accuracy": accuracy,
    }


def compact_by_field(records: list[dict[str, Any]], field: str, score_key: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        buckets[str(row.get(field))].append(row)
    output: list[dict[str, Any]] = []
    for key, rows in sorted(buckets.items()):
        scores = [float(row[score_key]) for row in rows]
        pred_abstain = sum(score < TAU_OBS for score in scores)
        output.append(
            {
                "field": field,
                "value": key,
                "score_id": score_key,
                "rows": len(rows),
                "obs_positive_rows": sum(int(row["obs_label"]) for row in rows),
                "mean_score": sum(scores) / max(len(scores), 1),
                "min_score": min(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
                "pred_abstain_rows": pred_abstain,
                "pred_abstain_rate": pred_abstain / max(len(rows), 1),
            }
        )
    return output


def risk_coverage_rows(records: list[dict[str, Any]], score_key: str) -> list[dict[str, Any]]:
    ordered = sorted(records, key=lambda row: float(row[score_key]), reverse=True)
    if not ordered:
        return []
    output: list[dict[str, Any]] = []
    n = len(ordered)
    for pct in [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        k = max(1, int(round(n * pct / 100)))
        selected = ordered[:k]
        unobservable = sum(1 for row in selected if int(row["obs_label"]) == 0)
        output.append(
            {
                "score_id": score_key,
                "coverage_pct": pct,
                "coverage": k / n,
                "selected_rows": k,
                "unobservable_rows": unobservable,
                "risk": unobservable / max(k, 1),
            }
        )
    return output


def aurc(curve: list[dict[str, Any]]) -> float:
    if not curve:
        return 0.0
    prev_cov = 0.0
    prev_risk = float(curve[0]["risk"])
    area = 0.0
    for row in curve:
        cov = float(row["coverage"])
        risk = float(row["risk"])
        area += (cov - prev_cov) * (prev_risk + risk) / 2.0
        prev_cov = cov
        prev_risk = risk
    return area


def reliability_diagram_rows(labels: list[int], scores: list[float], score_id: str, bins: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(bins):
        lo = idx / bins
        hi = (idx + 1) / bins
        indices = [i for i, score in enumerate(scores) if score >= lo and (score < hi or idx == bins - 1)]
        if not indices:
            rows.append({"score_id": score_id, "bin": idx, "lo": lo, "hi": hi, "rows": 0, "confidence": "", "accuracy": ""})
            continue
        confidence = sum(scores[i] for i in indices) / len(indices)
        accuracy = sum(labels[i] for i in indices) / len(indices)
        rows.append({"score_id": score_id, "bin": idx, "lo": lo, "hi": hi, "rows": len(indices), "confidence": confidence, "accuracy": accuracy})
    return rows


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    materialization_dir = resolve(repo_root, args.materialization_dir)
    schema_audit_dir = resolve(repo_root, args.schema_audit_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    materialization = read_json(materialization_dir / "materialization_manifest.json")
    audit = read_json(schema_audit_dir / "summary.json")
    if materialization.get("status") != EXPECTED_MATERIALIZATION_STATUS or materialization.get("validation_errors") != 0:
        errors.append({"error_type": "materialization_not_ready", "status": materialization.get("status"), "validation_errors": materialization.get("validation_errors")})
    if audit.get("status") != EXPECTED_SCHEMA_AUDIT_STATUS or audit.get("validation_errors") != 0:
        errors.append({"error_type": "schema_audit_not_ready", "status": audit.get("status"), "validation_errors": audit.get("validation_errors")})
    if not audit.get("boundary", {}).get("pobs_only_diagnostic_metric_allowed"):
        errors.append({"error_type": "pobs_only_metric_not_allowed_by_schema_audit"})

    hidden_rows = read_jsonl(materialization_dir / "hidden_observability_v2_labels.jsonl")
    train_rows = join_qe_hidden(read_jsonl(materialization_dir / "model_safe_qe_v2_train.jsonl"), hidden_rows, TRAIN_SPLIT)
    eval_rows = join_qe_hidden(read_jsonl(materialization_dir / "model_safe_qe_v2_eval.jsonl"), hidden_rows, EVAL_SPLIT)
    if not train_rows or not eval_rows:
        errors.append({"error_type": "missing_train_or_eval_rows", "train": len(train_rows), "eval": len(eval_rows)})
    if len(set(row["obs_label"] for row in train_rows)) < 2:
        errors.append({"error_type": "train_single_class", "counts": dict(Counter(row["obs_label"] for row in train_rows))})
    if len(set(row["obs_label"] for row in eval_rows)) < 2:
        errors.append({"error_type": "eval_single_class", "counts": dict(Counter(row["obs_label"] for row in eval_rows))})

    model, prior, fit_summary = fit_model(train_rows, qe_v2_features, args.epochs, args.lr, args.l2)
    learned_scores = predict_model(model, prior, eval_rows, qe_v2_features)
    state_scores = [qe_state_score(row) for row in eval_rows]
    legacy_scores = [1.0 for _ in eval_rows]
    labels = [int(row["obs_label"]) for row in eval_rows]

    records: list[dict[str, Any]] = []
    for row, learned, state, legacy in zip(eval_rows, learned_scores, state_scores, legacy_scores):
        records.append(
            {
                "candidate_id": row.get("candidate_id"),
                "source_candidate_id": row.get("source_candidate_id"),
                "route_family": row.get("route_family"),
                "predicate_label": row.get("predicate_label"),
                "control_type": row.get("control_type"),
                "row_role": row.get("row_role"),
                "observability_label": row.get("observability_label"),
                "q_e_state_v2_hidden": row.get("q_e_state_v2_hidden"),
                "q_e_state_source_hidden": row.get("q_e_state_source_hidden"),
                "obs_label": int(row["obs_label"]),
                "p_obs_learned": learned,
                "p_obs_qe_state_code": state,
                "p_obs_legacy_all_sufficient": legacy,
                "pred_abstain_learned": learned < TAU_OBS,
                "pred_abstain_qe_state_code": state < TAU_OBS,
                "pred_abstain_legacy_all_sufficient": legacy < TAU_OBS,
            }
        )

    pobs_metrics = [
        enrich_binary("official_validation_diagnostic_subset", "p_obs_learned", labels, learned_scores),
        enrich_binary("official_validation_diagnostic_subset", "p_obs_qe_state_code", labels, state_scores),
        enrich_binary("official_validation_diagnostic_subset", "p_obs_legacy_all_sufficient", labels, legacy_scores),
    ]
    threshold_rows = [
        threshold_metrics(records, "p_obs_learned"),
        threshold_metrics(records, "p_obs_qe_state_code"),
        threshold_metrics(records, "p_obs_legacy_all_sufficient"),
    ]
    curve = risk_coverage_rows(records, "p_obs_learned")
    state_curve = risk_coverage_rows(records, "p_obs_qe_state_code")
    legacy_curve = risk_coverage_rows(records, "p_obs_legacy_all_sufficient")
    label_metric_rows = compact_by_field(records, "observability_label", "p_obs_learned") + compact_by_field(records, "q_e_state_v2_hidden", "p_obs_learned")
    reliability_rows = (
        reliability_diagram_rows(labels, learned_scores, "p_obs_learned")
        + reliability_diagram_rows(labels, state_scores, "p_obs_qe_state_code")
        + reliability_diagram_rows(labels, legacy_scores, "p_obs_legacy_all_sufficient")
    )

    learned_metric = pobs_metrics[0]
    learned_thresh = threshold_rows[0]
    pass_checks = {
        "schema_gate_passed": not errors,
        "p_obs_auroc_ge_0_70": (learned_metric.get("auroc") or 0.0) >= 0.70,
        "abstain_recall_ge_0_70": learned_thresh["abstain_recall"] >= 0.70,
        "observable_false_abstain_le_0_30": learned_thresh["observable_false_abstain_rate"] <= 0.30,
        "p_obs_ece_le_0_20": learned_metric["ECE_10"] <= 0.20,
    }
    diagnostic_pass = all(pass_checks.values())

    write_csv(out / "pobs_metrics.csv", pobs_metrics)
    write_csv(out / "threshold_metrics.csv", threshold_rows)
    write_csv(out / "observability_label_metrics.csv", label_metric_rows)
    write_csv(out / "risk_coverage_curve.csv", curve + state_curve + legacy_curve)
    write_csv(out / "reliability_diagram.csv", reliability_rows)
    write_jsonl(out / "prediction_scores.jsonl", records)
    write_jsonl(out / "validation_errors.jsonl", errors)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "source_artifacts": {
            "materialization": repo_rel(repo_root, materialization_dir),
            "schema_audit": repo_rel(repo_root, schema_audit_dir),
        },
        "row_counts": {
            "train_rows": len(train_rows),
            "eval_rows": len(eval_rows),
            "train_label_counts": dict(sorted(Counter(row["observability_label"] for row in train_rows).items())),
            "eval_label_counts": dict(sorted(Counter(row["observability_label"] for row in eval_rows).items())),
            "eval_obs_counts": dict(sorted(Counter(str(row["obs_label"]) for row in eval_rows).items())),
        },
        "fit_summary": fit_summary,
        "primary_metrics": {
            "p_obs_auroc": learned_metric.get("auroc"),
            "p_obs_ece_10": learned_metric.get("ECE_10"),
            "p_obs_brier": learned_metric.get("Brier"),
            "p_obs_nll": learned_metric.get("NLL"),
            "abstain_precision": learned_thresh["abstain_precision"],
            "abstain_recall": learned_thresh["abstain_recall"],
            "observable_false_abstain_rate": learned_thresh["observable_false_abstain_rate"],
            "false_observable_rate": learned_thresh["false_observable_rate"],
            "AURC": aurc(curve),
        },
        "baseline_metrics": {
            "direct_qe_state_code_auroc": pobs_metrics[1].get("auroc"),
            "direct_qe_state_code_ece_10": pobs_metrics[1].get("ECE_10"),
            "legacy_all_sufficient_auroc": pobs_metrics[2].get("auroc"),
            "legacy_all_sufficient_abstain_recall": threshold_rows[2]["abstain_recall"],
        },
        "pass_checks": pass_checks,
        "diagnostic_pass": diagnostic_pass,
        "boundary": {
            "pobs_only_diagnostic_metric_allowed": True,
            "full_selective_decision_rerun_allowed": diagnostic_pass,
            "paper_level_pobs_prel_solved_claim_allowed": False,
            "official_test_used": False,
            "eval_qe_v2_uses_audit_proxy": True,
            "diagnostic_feature_policy": "Q_e v2 only; qe_v2_diagnostic_source excluded from model input",
        },
        "decision": {
            "selected_path": "pobs_repair_diagnostic_pass_review_before_selective_rerun" if diagnostic_pass else "pobs_repair_failed_fix_qe_or_labels",
            "next_todo": "pobs_prel_qe_repair_pobs_metric_review" if diagnostic_pass else "pobs_prel_qe_repair_pobs_failure_review",
        },
        "outputs": {
            "pobs_metrics": repo_rel(repo_root, out / "pobs_metrics.csv"),
            "threshold_metrics": repo_rel(repo_root, out / "threshold_metrics.csv"),
            "observability_label_metrics": repo_rel(repo_root, out / "observability_label_metrics.csv"),
            "risk_coverage_curve": repo_rel(repo_root, out / "risk_coverage_curve.csv"),
            "reliability_diagram": repo_rel(repo_root, out / "reliability_diagram.csv"),
            "prediction_scores": repo_rel(repo_root, out / "prediction_scores.jsonl"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "manifest": repo_rel(repo_root, out / "metric_manifest.json"),
        },
    }
    write_json(out / "metric_manifest.json", manifest)
    write_json(out / "gate_decision.json", manifest)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
