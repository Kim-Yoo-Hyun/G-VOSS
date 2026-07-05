#!/usr/bin/env python3
"""Run H002 p_obs / p_rel selective-decision metrics."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_grouped_eval import binary_metrics, fit_model, merge_features, predict_model, q_features, read_jsonl, t_features, z_features
from run_official_metric import common_g_features, compatibility_features


SCHEMA_VERSION = "h002_pobs_prel_selective_metric_v1"
STATUS_READY = "h002_pobs_prel_selective_metric_ready"
STATUS_ERROR = "h002_pobs_prel_selective_metric_errors"
EXPECTED_AUDIT_STATUS = "h002_pobs_prel_schema_audit_ready"
TRAIN_SPLIT = "internal_train"
EVAL_SPLIT = "official_validation"
TAU_OBS = 0.5
TAU_REL = 0.5


FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--schema-audit-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def join_views(materialization_dir: Path) -> list[dict[str, Any]]:
    qe = {row["candidate_id"]: row for row in iter_jsonl(materialization_dir / "model_safe_qe_view.jsonl")}
    prel = {row["candidate_id"]: row for row in iter_jsonl(materialization_dir / "model_safe_prel_view.jsonl")}
    hidden = {row["candidate_id"]: row for row in iter_jsonl(materialization_dir / "hidden_selective_labels.jsonl")}
    ids = sorted(set(qe) & set(prel) & set(hidden))
    rows: list[dict[str, Any]] = []
    for candidate_id in ids:
        base = dict(prel[candidate_id])
        base["feature_blocks"] = dict(prel[candidate_id].get("feature_blocks") or {})
        base["feature_blocks"]["Q_e"] = (qe[candidate_id].get("feature_blocks") or {}).get("Q_e", {})
        base["obs_label"] = int(hidden[candidate_id]["obs_label"])
        base["rel_label"] = hidden[candidate_id].get("rel_label")
        base["decision_label"] = hidden[candidate_id]["decision_label"]
        base["control_type"] = hidden[candidate_id]["control_type"]
        base["row_role"] = hidden[candidate_id]["row_role"]
        rows.append(base)
    return rows


def pobs_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return q_features(row)


def prel_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), common_g_features(row), compatibility_features(row), q_features(row), z_features(row))


def ece(labels: list[int], scores: list[float], bins: int = 10) -> float:
    if not labels:
        return 0.0
    total = len(labels)
    out = 0.0
    for i in range(bins):
        lo = i / bins
        hi = (i + 1) / bins
        idx = [j for j, score in enumerate(scores) if (score >= lo and (score < hi or i == bins - 1))]
        if not idx:
            continue
        conf = sum(scores[j] for j in idx) / len(idx)
        acc = sum(labels[j] for j in idx) / len(idx)
        out += len(idx) / total * abs(conf - acc)
    return out


def enrich_binary_metrics(scope: str, metric_name: str, labels: list[int], scores: list[float]) -> dict[str, Any]:
    metrics = binary_metrics(labels, scores)
    metrics["scope"] = scope
    metrics["metric_name"] = metric_name
    metrics["ECE_10"] = ece(labels, scores)
    return metrics


def decision_pred(p_obs: float, p_rel: float) -> str:
    if p_obs < TAU_OBS:
        return "abstain"
    return "accept" if p_rel >= TAU_REL else "reject"


def multiclass_metrics(labels: list[str], preds: list[str]) -> dict[str, Any]:
    classes = ["accept", "reject", "abstain"]
    rows: dict[str, dict[str, int]] = {}
    f1s: list[float] = []
    for cls in classes:
        tp = sum(1 for y, p in zip(labels, preds) if y == cls and p == cls)
        fp = sum(1 for y, p in zip(labels, preds) if y != cls and p == cls)
        fn = sum(1 for y, p in zip(labels, preds) if y == cls and p != cls)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        rows[cls] = {"tp": tp, "fp": fp, "fn": fn}
        f1s.append(f1)
    return {
        "rows": len(labels),
        "accuracy": sum(1 for y, p in zip(labels, preds) if y == p) / max(len(labels), 1),
        "macro_F1": sum(f1s) / len(f1s),
        "accept_tp": rows["accept"]["tp"],
        "reject_tp": rows["reject"]["tp"],
        "abstain_tp": rows["abstain"]["tp"],
    }


def risk_coverage_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(records, key=lambda row: row["p_obs"], reverse=True)
    out: list[dict[str, Any]] = []
    if not ordered:
        return out
    checkpoints = sorted(set([1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]))
    n = len(ordered)
    for pct in checkpoints:
        k = max(1, int(round(n * pct / 100)))
        decided = ordered[:k]
        errors = sum(1 for row in decided if row["pred_decision"] != row["decision_label"])
        out.append({
            "coverage_pct": pct,
            "coverage": k / n,
            "risk": errors / max(k, 1),
            "decided_rows": k,
            "errors": errors,
        })
    return out


def aurc(curve: list[dict[str, Any]]) -> float:
    if not curve:
        return 0.0
    prev_cov = 0.0
    area = 0.0
    prev_risk = float(curve[0]["risk"])
    for row in curve:
        cov = float(row["coverage"])
        risk = float(row["risk"])
        area += (cov - prev_cov) * (prev_risk + risk) / 2.0
        prev_cov = cov
        prev_risk = risk
    return area


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    materialization_dir = args.materialization_dir if args.materialization_dir.is_absolute() else repo_root / args.materialization_dir
    schema_audit_dir = args.schema_audit_dir if args.schema_audit_dir.is_absolute() else repo_root / args.schema_audit_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    audit = read_json(schema_audit_dir / "summary.json")
    if audit.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error": "unexpected_schema_audit_status", "observed": audit.get("status")})

    rows = join_views(materialization_dir)
    pobs_train = [dict(row, target_y=int(row["obs_label"])) for row in rows if row["eval_split"] == TRAIN_SPLIT]
    pobs_eval = [row for row in rows if row["eval_split"] == EVAL_SPLIT]
    prel_train = [dict(row, target_y=int(row["rel_label"])) for row in rows if row["eval_split"] == TRAIN_SPLIT and row["obs_label"] == 1 and row["rel_label"] is not None]
    prel_eval = [row for row in rows if row["eval_split"] == EVAL_SPLIT and row["obs_label"] == 1 and row["rel_label"] is not None]

    if not pobs_train or not pobs_eval:
        errors.append({"error": "missing_pobs_train_or_eval", "train": len(pobs_train), "eval": len(pobs_eval)})
    if not prel_train or not prel_eval:
        errors.append({"error": "missing_prel_train_or_eval", "train": len(prel_train), "eval": len(prel_eval)})

    pobs_model, pobs_prior, pobs_fit = fit_model(pobs_train, pobs_feature_fn, args.epochs, args.lr, args.l2)
    prel_model, prel_prior, prel_fit = fit_model(prel_train, prel_feature_fn, args.epochs, args.lr, args.l2)

    pobs_scores = predict_model(pobs_model, pobs_prior, pobs_eval, pobs_feature_fn)
    prel_scores = predict_model(prel_model, prel_prior, prel_eval, prel_feature_fn)
    prel_by_id = {row["candidate_id"]: score for row, score in zip(prel_eval, prel_scores)}

    eval_records: list[dict[str, Any]] = []
    for row, p_obs in zip(pobs_eval, pobs_scores):
        p_rel = prel_by_id.get(row["candidate_id"], prel_prior)
        pred = decision_pred(p_obs, p_rel)
        eval_records.append({
            "candidate_id": row["candidate_id"],
            "source_candidate_id": row.get("source_candidate_id"),
            "route_family": row.get("route_family"),
            "predicate_label": row.get("predicate_label"),
            "control_type": row.get("control_type"),
            "row_role": row.get("row_role"),
            "obs_label": int(row["obs_label"]),
            "rel_label": row.get("rel_label"),
            "decision_label": row["decision_label"],
            "p_obs": p_obs,
            "p_rel": p_rel,
            "pred_decision": pred,
        })

    pobs_labels = [int(row["obs_label"]) for row in pobs_eval]
    pobs_metric = enrich_binary_metrics("official_validation_all", "p_obs", pobs_labels, pobs_scores)
    prel_labels = [int(row["rel_label"]) for row in prel_eval]
    prel_metric = enrich_binary_metrics("official_validation_observable", "p_rel", prel_labels, prel_scores)
    decision_metric = multiclass_metrics([row["decision_label"] for row in eval_records], [row["pred_decision"] for row in eval_records])
    decision_metric.update({"scope": "official_validation_all", "metric_name": "accept_reject_abstain"})

    control_rows: list[dict[str, Any]] = []
    by_control: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eval_records:
        by_control[str(row["control_type"])].append(row)
    original_median = median([row["p_obs"] for row in by_control.get("observed_original", [])])
    for control, bucket in sorted(by_control.items()):
        scores = [row["p_obs"] for row in bucket]
        abstain_rate = sum(1 for row in bucket if row["pred_decision"] == "abstain") / max(len(bucket), 1)
        control_rows.append({
            "control_type": control,
            "rows": len(bucket),
            "median_p_obs": median(scores),
            "delta_vs_observed_median": median(scores) - original_median,
            "abstain_rate": abstain_rate,
        })

    curve = risk_coverage_rows(eval_records)
    aurc_value = aurc(curve)
    pass_checks = {
        "p_obs_auroc_ge_0_95": (pobs_metric.get("auroc") or 0.0) >= 0.95,
        "p_rel_auroc_ge_0_70": (prel_metric.get("auroc") or 0.0) >= 0.70,
        "decision_macro_f1_ge_0_70": decision_metric["macro_F1"] >= 0.70,
        "missing_controls_abstain_ge_0_90": all(
            row["abstain_rate"] >= 0.90 for row in control_rows if row["control_type"] != "observed_original"
        ),
        "calibration_ece_warn_only_le_0_15": (pobs_metric["ECE_10"] <= 0.15 and prel_metric["ECE_10"] <= 0.15),
    }
    selective_metric_pass = (
        pass_checks["p_obs_auroc_ge_0_95"]
        and pass_checks["p_rel_auroc_ge_0_70"]
        and pass_checks["decision_macro_f1_ge_0_70"]
        and pass_checks["missing_controls_abstain_ge_0_90"]
    )
    paper_promotion_pass = selective_metric_pass and pass_checks["calibration_ece_warn_only_le_0_15"]

    write_csv(out / "pobs_metrics.csv", [pobs_metric])
    write_csv(out / "prel_metrics.csv", [prel_metric])
    write_csv(out / "decision_metrics.csv", [decision_metric])
    write_csv(out / "missing_evidence_control_metrics.csv", control_rows)
    write_csv(out / "risk_coverage_curve.csv", curve)
    write_jsonl(out / "prediction_scores.jsonl", eval_records)
    write_jsonl(out / "validation_errors.jsonl", errors)
    gate = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "materialization_dir": rel_path(repo_root, materialization_dir),
        "schema_audit_dir": rel_path(repo_root, schema_audit_dir),
        "fit_summary": {"p_obs": pobs_fit, "p_rel": prel_fit},
        "row_counts": {
            "pobs_train": len(pobs_train),
            "pobs_eval": len(pobs_eval),
            "prel_train": len(prel_train),
            "prel_eval": len(prel_eval),
            "eval_records": len(eval_records),
        },
        "primary_metrics": {
            "p_obs_auroc": pobs_metric.get("auroc"),
            "p_obs_ece_10": pobs_metric.get("ECE_10"),
            "p_rel_auroc": prel_metric.get("auroc"),
            "p_rel_ece_10": prel_metric.get("ECE_10"),
            "decision_macro_F1": decision_metric["macro_F1"],
            "decision_accuracy": decision_metric["accuracy"],
            "AURC": aurc_value,
        },
        "pass_checks": pass_checks,
        "selective_metric_pass": selective_metric_pass,
        "paper_promotion_pass": paper_promotion_pass,
        "claim_boundary": {
            "synthetic_missing_evidence_controls_used": True,
            "independent_human_observability_labels_used": False,
            "pobs_prel_quantitative_result_claim_allowed": paper_promotion_pass,
            "paper_promotion_blocker": None if paper_promotion_pass else "calibration_or_proxy_label_boundary_review_required",
            "official_test_used": False,
        },
        "outputs": {
            "pobs_metrics": rel_path(repo_root, out / "pobs_metrics.csv"),
            "prel_metrics": rel_path(repo_root, out / "prel_metrics.csv"),
            "decision_metrics": rel_path(repo_root, out / "decision_metrics.csv"),
            "missing_evidence_control_metrics": rel_path(repo_root, out / "missing_evidence_control_metrics.csv"),
            "risk_coverage_curve": rel_path(repo_root, out / "risk_coverage_curve.csv"),
            "prediction_scores": rel_path(repo_root, out / "prediction_scores.jsonl"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
        "next_todo": "compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner",
    }
    write_json(out / "gate_decision.json", gate)
    write_json(out / "eval_manifest.json", gate)
    return 1 if errors else 0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


if __name__ == "__main__":
    raise SystemExit(main())
