#!/usr/bin/env python3
"""Evaluate p_obs / p_rel on user-confirmed observability audit labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_official_metric import common_g_features, compatibility_features
from run_pobs_prel_selective_metric import (
    TAU_OBS,
    TAU_REL,
    aurc,
    decision_pred,
    enrich_binary_metrics,
    iter_jsonl,
    median,
    multiclass_metrics,
    pobs_feature_fn,
    prel_feature_fn,
    risk_coverage_rows,
)
from run_grouped_eval import fit_model, merge_features, predict_model, q_features, t_features, z_features


SCHEMA_VERSION = "h002_pobs_prel_observability_metric_v1"
STATUS_READY = "h002_pobs_prel_observability_metric_ready"
STATUS_ERROR = "h002_pobs_prel_observability_metric_errors"
EXPECTED_TRAIN_SCHEMA_STATUS = "h002_pobs_prel_schema_audit_ready"
EXPECTED_EVAL_SCHEMA_STATUS = "h002_pobs_prel_observability_schema_audit_ready"
EXPECTED_GATE_STATUS = "h002_pobs_prel_observability_metric_gate_ready"
TRAIN_SPLIT = "internal_train"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--train-materialization-dir", type=Path, required=True)
    parser.add_argument("--train-schema-audit-dir", type=Path, required=True)
    parser.add_argument("--eval-ingestion-dir", type=Path, required=True)
    parser.add_argument("--eval-schema-audit-dir", type=Path, required=True)
    parser.add_argument("--metric-gate-dir", type=Path, required=True)
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
    return json.loads(path.read_text(encoding="utf-8"))


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def join_train_views(materialization_dir: Path) -> list[dict[str, Any]]:
    qe = {row["candidate_id"]: row for row in iter_jsonl(materialization_dir / "model_safe_qe_view.jsonl")}
    prel = {row["candidate_id"]: row for row in iter_jsonl(materialization_dir / "model_safe_prel_view.jsonl")}
    hidden = {row["candidate_id"]: row for row in iter_jsonl(materialization_dir / "hidden_selective_labels.jsonl")}
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted(set(qe) & set(prel) & set(hidden)):
        base = dict(prel[candidate_id])
        base["feature_blocks"] = dict(prel[candidate_id].get("feature_blocks") or {})
        base["feature_blocks"]["Q_e"] = (qe[candidate_id].get("feature_blocks") or {}).get("Q_e", {})
        base["obs_label"] = int(hidden[candidate_id]["obs_label"])
        base["rel_label"] = hidden[candidate_id].get("rel_label")
        base["decision_label"] = hidden[candidate_id]["decision_label"]
        base["control_type"] = hidden[candidate_id].get("control_type") or base.get("control_type")
        base["row_role"] = hidden[candidate_id].get("row_role") or base.get("row_role")
        rows.append(base)
    return rows


def join_eval_views(ingestion_dir: Path) -> list[dict[str, Any]]:
    qe = {row["candidate_id"]: row for row in iter_jsonl(ingestion_dir / "model_safe_qe_view.jsonl")}
    prel = {row["candidate_id"]: row for row in iter_jsonl(ingestion_dir / "model_safe_prel_view.jsonl")}
    hidden = {row["candidate_id"]: row for row in iter_jsonl(ingestion_dir / "hidden_observability_labels.jsonl")}
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted(set(qe) & set(prel) & set(hidden)):
        label = hidden[candidate_id]
        base = dict(prel[candidate_id])
        base["feature_blocks"] = dict(prel[candidate_id].get("feature_blocks") or {})
        base["feature_blocks"]["Q_e"] = (qe[candidate_id].get("feature_blocks") or {}).get("Q_e", {})
        base["obs_label"] = int(label["obs_label"])
        base["rel_label"] = label.get("rel_label")
        base["decision_label"] = label["decision_label"]
        base["control_type"] = base.get("control_type") or "observed_original"
        base["row_role"] = label.get("row_role") or base.get("row_role")
        base["queue_kind"] = label.get("queue_kind")
        base["observability_label"] = label.get("observability_label")
        base["raw_human_confirmed"] = label.get("human_confirmed")
        base["user_confirmed_for_metric"] = True
        rows.append(base)
    return rows


def compact_by_field(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        buckets[str(row.get(field))].append(row)
    for key, rows in sorted(buckets.items()):
        pobs = [float(row["p_obs"]) for row in rows]
        prel = [float(row["p_rel"]) for row in rows]
        decisions = Counter(str(row["decision_label"]) for row in rows)
        preds = Counter(str(row["pred_decision"]) for row in rows)
        out.append(
            {
                field: key,
                "rows": len(rows),
                "obs_positive_rows": sum(int(row["obs_label"]) for row in rows),
                "median_p_obs": median(pobs),
                "median_p_rel": median(prel),
                "decision_counts": dict(sorted(decisions.items())),
                "pred_decision_counts": dict(sorted(preds.items())),
                "abstain_rate": preds.get("abstain", 0) / max(len(rows), 1),
            }
        )
    return out


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    train_dir = resolve(repo_root, args.train_materialization_dir)
    train_schema_dir = resolve(repo_root, args.train_schema_audit_dir)
    eval_dir = resolve(repo_root, args.eval_ingestion_dir)
    eval_schema_dir = resolve(repo_root, args.eval_schema_audit_dir)
    gate_dir = resolve(repo_root, args.metric_gate_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    train_schema = read_json(train_schema_dir / "summary.json")
    eval_schema = read_json(eval_schema_dir / "summary.json")
    gate = read_json(gate_dir / "summary.json")
    if train_schema.get("status") != EXPECTED_TRAIN_SCHEMA_STATUS or train_schema.get("validation_errors") != 0:
        errors.append({"error": "train_schema_not_ready", "status": train_schema.get("status")})
    if eval_schema.get("status") != EXPECTED_EVAL_SCHEMA_STATUS or eval_schema.get("validation_errors") != 0:
        errors.append({"error": "eval_schema_not_ready", "status": eval_schema.get("status")})
    if gate.get("status") != EXPECTED_GATE_STATUS or not gate.get("boundary", {}).get("metric_rerun_allowed_now"):
        errors.append({"error": "metric_gate_not_open", "status": gate.get("status")})

    train_rows = join_train_views(train_dir)
    eval_rows = join_eval_views(eval_dir)
    pobs_train = [dict(row, target_y=int(row["obs_label"])) for row in train_rows if row.get("eval_split") == TRAIN_SPLIT]
    pobs_eval = eval_rows
    prel_train = [
        dict(row, target_y=int(row["rel_label"]))
        for row in train_rows
        if row.get("eval_split") == TRAIN_SPLIT and row.get("obs_label") == 1 and row.get("rel_label") is not None
    ]
    prel_eval = [row for row in eval_rows if row.get("obs_label") == 1 and row.get("rel_label") is not None]
    if not pobs_train or not pobs_eval:
        errors.append({"error": "missing_pobs_rows", "train": len(pobs_train), "eval": len(pobs_eval)})
    if not prel_train or not prel_eval:
        errors.append({"error": "missing_prel_rows", "train": len(prel_train), "eval": len(prel_eval)})

    pobs_model, pobs_prior, pobs_fit = fit_model(pobs_train, pobs_feature_fn, args.epochs, args.lr, args.l2)
    prel_model, prel_prior, prel_fit = fit_model(prel_train, prel_feature_fn, args.epochs, args.lr, args.l2)
    pobs_scores = predict_model(pobs_model, pobs_prior, pobs_eval, pobs_feature_fn)
    prel_scores = predict_model(prel_model, prel_prior, prel_eval, prel_feature_fn)
    prel_by_id = {row["candidate_id"]: score for row, score in zip(prel_eval, prel_scores)}

    eval_records: list[dict[str, Any]] = []
    for row, p_obs in zip(pobs_eval, pobs_scores):
        p_rel = prel_by_id.get(row["candidate_id"], prel_prior)
        eval_records.append(
            {
                "candidate_id": row["candidate_id"],
                "source_candidate_id": row.get("source_candidate_id"),
                "scan_id": row.get("scan_id"),
                "route_family": row.get("route_family"),
                "predicate_label": row.get("predicate_label"),
                "queue_kind": row.get("queue_kind"),
                "observability_label": row.get("observability_label"),
                "obs_label": int(row["obs_label"]),
                "rel_label": row.get("rel_label"),
                "decision_label": row["decision_label"],
                "p_obs": p_obs,
                "p_rel": p_rel,
                "pred_decision": decision_pred(p_obs, p_rel),
            }
        )

    pobs_metric = enrich_binary_metrics(
        "user_confirmed_observability_subset",
        "p_obs",
        [int(row["obs_label"]) for row in pobs_eval],
        pobs_scores,
    )
    prel_metric = enrich_binary_metrics(
        "user_confirmed_observable_subset",
        "p_rel",
        [int(row["rel_label"]) for row in prel_eval],
        prel_scores,
    )
    decision_metric = multiclass_metrics(
        [row["decision_label"] for row in eval_records],
        [row["pred_decision"] for row in eval_records],
    )
    decision_metric.update({"scope": "user_confirmed_observability_subset", "metric_name": "accept_reject_abstain"})

    curve = risk_coverage_rows(eval_records)
    pass_checks = {
        "p_obs_auroc_ge_0_70": (pobs_metric.get("auroc") or 0.0) >= 0.70,
        "p_rel_auroc_ge_0_70": (prel_metric.get("auroc") or 0.0) >= 0.70,
        "decision_macro_f1_ge_0_50": decision_metric["macro_F1"] >= 0.50,
        "schema_gate_passed": not errors,
    }
    diagnostic_metric_pass = all(pass_checks.values())
    paper_promotion_pass = False

    write_csv(out / "pobs_metrics.csv", [pobs_metric])
    write_csv(out / "prel_metrics.csv", [prel_metric])
    write_csv(out / "decision_metrics.csv", [decision_metric])
    write_csv(out / "queue_kind_metrics.csv", compact_by_field(eval_records, "queue_kind"))
    write_csv(out / "observability_label_metrics.csv", compact_by_field(eval_records, "observability_label"))
    write_csv(out / "risk_coverage_curve.csv", curve)
    write_jsonl(out / "prediction_scores.jsonl", eval_records)
    write_jsonl(out / "validation_errors.jsonl", errors)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": {
            "train_materialization": repo_rel(repo_root, train_dir),
            "train_schema_audit": repo_rel(repo_root, train_schema_dir),
            "eval_ingestion": repo_rel(repo_root, eval_dir),
            "eval_schema_audit": repo_rel(repo_root, eval_schema_dir),
            "metric_gate": repo_rel(repo_root, gate_dir),
        },
        "row_counts": {
            "pobs_train": len(pobs_train),
            "pobs_eval": len(pobs_eval),
            "prel_train": len(prel_train),
            "prel_eval": len(prel_eval),
            "eval_records": len(eval_records),
            "eval_label_counts": dict(sorted(Counter(row["observability_label"] for row in eval_records).items())),
            "eval_decision_counts": dict(sorted(Counter(row["decision_label"] for row in eval_records).items())),
        },
        "fit_summary": {"p_obs": pobs_fit, "p_rel": prel_fit},
        "primary_metrics": {
            "p_obs_auroc": pobs_metric.get("auroc"),
            "p_obs_ece_10": pobs_metric.get("ECE_10"),
            "p_rel_auroc": prel_metric.get("auroc"),
            "p_rel_ece_10": prel_metric.get("ECE_10"),
            "decision_macro_F1": decision_metric["macro_F1"],
            "decision_accuracy": decision_metric["accuracy"],
            "AURC": aurc(curve),
        },
        "pass_checks": pass_checks,
        "diagnostic_metric_pass": diagnostic_metric_pass,
        "paper_promotion_pass": paper_promotion_pass,
        "claim_boundary": {
            "user_confirmed_codex_labels_used": True,
            "independent_human_authored_label_file": False,
            "official_test_used": False,
            "diagnostic_metric_allowed": True,
            "pobs_prel_quantitative_paper_claim_allowed": False,
            "paper_promotion_blocker": "diagnostic_subset_only_and_labels_originated_from_codex_fill",
        },
        "outputs": {
            "pobs_metrics": repo_rel(repo_root, out / "pobs_metrics.csv"),
            "prel_metrics": repo_rel(repo_root, out / "prel_metrics.csv"),
            "decision_metrics": repo_rel(repo_root, out / "decision_metrics.csv"),
            "queue_kind_metrics": repo_rel(repo_root, out / "queue_kind_metrics.csv"),
            "observability_label_metrics": repo_rel(repo_root, out / "observability_label_metrics.csv"),
            "risk_coverage_curve": repo_rel(repo_root, out / "risk_coverage_curve.csv"),
            "prediction_scores": repo_rel(repo_root, out / "prediction_scores.jsonl"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
        "next_todo": "pobs_prel_observability_metric_result_review",
    }
    write_json(out / "metric_manifest.json", manifest)
    write_json(out / "gate_decision.json", manifest)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
