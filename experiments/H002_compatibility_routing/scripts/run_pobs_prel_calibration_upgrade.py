#!/usr/bin/env python3
"""Run H002 p_obs / p_rel calibration and observability-upgrade checks.

This runner is intentionally separate from the existing p_obs/p_rel stress-test
runner. It freezes internal train/dev as model/calibration splits, evaluates on
official validation, and adds an asset-based observability audit using actual
3RScan scan/multiview files.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_grouped_eval import binary_metrics, fit_model, merge_features, predict_model, q_features, t_features, z_features
from run_official_metric import common_g_features, compatibility_features
from run_pobs_prel_selective_metric import join_views, multiclass_metrics


SCHEMA_VERSION = "h002_pobs_prel_calibration_upgrade_v1"
STATUS_READY = "h002_pobs_prel_calibration_upgrade_ready"
STATUS_ERROR = "h002_pobs_prel_calibration_upgrade_errors"

TRAIN_SPLIT = "internal_train"
CALIB_SPLIT = "internal_dev"
EVAL_SPLIT = "official_validation"
TAU_OBS = 0.5
TAU_REL = 0.5
BOOTSTRAP_SEED = 20260704
BOOTSTRAP_N = 500
INSTANCE_RE = re.compile(r"instance_(\d+)_class_")


FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--schema-audit-dir", type=Path, required=True)
    parser.add_argument("--scan-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def clipped(p: float, eps: float = 1e-6) -> float:
    return min(max(float(p), eps), 1.0 - eps)


def logit(p: float) -> float:
    p = clipped(p)
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def nll(labels: list[int], scores: list[float]) -> float:
    if not labels:
        return 0.0
    total = 0.0
    for y, p in zip(labels, scores):
        p = clipped(p)
        total += -(y * math.log(p) + (1 - y) * math.log(1.0 - p))
    return total / len(labels)


def brier(labels: list[int], scores: list[float]) -> float:
    if not labels:
        return 0.0
    return sum((float(y) - float(p)) ** 2 for y, p in zip(labels, scores)) / len(labels)


def ece(labels: list[int], scores: list[float], bins: int = 10) -> float:
    if not labels:
        return 0.0
    total = len(labels)
    out = 0.0
    for i in range(bins):
        lo = i / bins
        hi = (i + 1) / bins
        idx = [j for j, score in enumerate(scores) if score >= lo and (score < hi or i == bins - 1)]
        if not idx:
            continue
        conf = sum(scores[j] for j in idx) / len(idx)
        acc = sum(labels[j] for j in idx) / len(idx)
        out += len(idx) / total * abs(conf - acc)
    return out


def metric_row(scope: str, name: str, labels: list[int], scores: list[float]) -> dict[str, Any]:
    row = binary_metrics(labels, scores)
    row.update(
        {
            "scope": scope,
            "metric_name": name,
            "ECE_10": ece(labels, scores),
            "Brier": brier(labels, scores),
            "NLL": nll(labels, scores),
        }
    )
    return row


def pobs_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return q_features(row)


def prel_feature_fn(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), common_g_features(row), compatibility_features(row), q_features(row), z_features(row))


def predict_one(model: Any, prior: float, row: dict[str, Any], feature_fn: FeatureFn) -> float:
    if model is None:
        return prior
    return float(model.predict_one(feature_fn(row)))


@dataclass
class Calibrator:
    name: str
    params: dict[str, Any]
    xs: list[float] | None = None
    ys: list[float] | None = None

    def transform_one(self, score: float) -> float:
        score = clipped(score)
        if self.name == "raw":
            return score
        if self.name == "temperature":
            return sigmoid(logit(score) / float(self.params["T"]))
        if self.name == "isotonic":
            assert self.xs is not None and self.ys is not None
            idx = bisect.bisect_left(self.xs, score)
            if idx <= 0:
                return clipped(self.ys[0])
            if idx >= len(self.xs):
                return clipped(self.ys[-1])
            return clipped(self.ys[idx])
        raise ValueError(f"unknown calibrator {self.name}")

    def transform(self, scores: list[float]) -> list[float]:
        return [self.transform_one(score) for score in scores]


def fit_temperature(labels: list[int], scores: list[float]) -> Calibrator:
    grid = [0.25, 0.35, 0.5, 0.7, 0.85, 1.0, 1.25, 1.5, 2.0, 2.5, 3.5, 5.0, 7.5, 10.0]
    best_t = 1.0
    best_nll = float("inf")
    for t in grid:
        transformed = [sigmoid(logit(score) / t) for score in scores]
        score_nll = nll(labels, transformed)
        if score_nll < best_nll:
            best_t = t
            best_nll = score_nll
    return Calibrator("temperature", {"T": best_t, "calibration_nll": best_nll})


def fit_isotonic(labels: list[int], scores: list[float]) -> Calibrator:
    ordered = sorted(zip(scores, labels), key=lambda item: item[0])
    blocks: list[dict[str, float]] = []
    for score, label in ordered:
        blocks.append({"lo": score, "hi": score, "sum_y": float(label), "weight": 1.0, "value": float(label)})
        while len(blocks) >= 2 and blocks[-2]["value"] > blocks[-1]["value"]:
            b2 = blocks.pop()
            b1 = blocks.pop()
            merged = {
                "lo": b1["lo"],
                "hi": b2["hi"],
                "sum_y": b1["sum_y"] + b2["sum_y"],
                "weight": b1["weight"] + b2["weight"],
                "value": 0.0,
            }
            merged["value"] = merged["sum_y"] / merged["weight"]
            blocks.append(merged)
    xs = [float(block["hi"]) for block in blocks]
    ys = [clipped(float(block["value"])) for block in blocks]
    return Calibrator("isotonic", {"block_count": len(blocks)}, xs=xs, ys=ys)


def select_calibrator(labels: list[int], scores: list[float]) -> tuple[Calibrator, list[dict[str, Any]]]:
    candidates = [Calibrator("raw", {}), fit_temperature(labels, scores), fit_isotonic(labels, scores)]
    rows: list[dict[str, Any]] = []
    for cal in candidates:
        transformed = cal.transform(scores)
        rows.append(
            {
                "calibrator": cal.name,
                "params": json.dumps(cal.params, sort_keys=True),
                "calibration_ECE_10": ece(labels, transformed),
                "calibration_Brier": brier(labels, transformed),
                "calibration_NLL": nll(labels, transformed),
            }
        )
    selected_row = min(rows, key=lambda row: (float(row["calibration_NLL"]), float(row["calibration_ECE_10"])))
    selected = next(cal for cal in candidates if cal.name == selected_row["calibrator"])
    return selected, rows


def decision_pred(p_obs: float, p_rel: float) -> str:
    if p_obs < TAU_OBS:
        return "abstain"
    return "accept" if p_rel >= TAU_REL else "reject"


def risk_coverage_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(records, key=lambda row: row["p_obs_calibrated"], reverse=True)
    out: list[dict[str, Any]] = []
    if not ordered:
        return out
    n = len(ordered)
    for pct in [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        k = max(1, int(round(n * pct / 100)))
        decided = ordered[:k]
        errors = sum(1 for row in decided if row["pred_decision_calibrated"] != row["decision_label"])
        out.append({"coverage_pct": pct, "coverage": k / n, "risk": errors / max(k, 1), "decided_rows": k, "errors": errors})
    return out


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


def reliability_diagram(labels: list[int], scores: list[float], scope: str, metric_name: str, bins: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in range(bins):
        lo = i / bins
        hi = (i + 1) / bins
        idx = [j for j, score in enumerate(scores) if score >= lo and (score < hi or i == bins - 1)]
        rows.append(
            {
                "scope": scope,
                "metric_name": metric_name,
                "bin": i,
                "lo": lo,
                "hi": hi,
                "count": len(idx),
                "avg_confidence": sum(scores[j] for j in idx) / len(idx) if idx else "",
                "empirical_accuracy": sum(labels[j] for j in idx) / len(idx) if idx else "",
            }
        )
    return rows


def bootstrap_ci(labels: list[int], scores: list[float], metric_name: str, seed: int = BOOTSTRAP_SEED, n_bootstrap: int = BOOTSTRAP_N) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    n = len(labels)
    if n == 0:
        return []
    dists: dict[str, list[float]] = defaultdict(list)
    for _ in range(n_bootstrap):
        idx = [rng.randrange(n) for _ in range(n)]
        bs_labels = [labels[i] for i in idx]
        bs_scores = [scores[i] for i in idx]
        row = metric_row("bootstrap", metric_name, bs_labels, bs_scores)
        for key in ["auroc", "auprc", "balanced_accuracy", "macro_F1", "Brier", "NLL", "ECE_10"]:
            value = row.get(key)
            if value is not None and value != "":
                dists[key].append(float(value))
    point = metric_row("point", metric_name, labels, scores)
    rows: list[dict[str, Any]] = []
    for key, values in dists.items():
        values.sort()
        lo = values[int(0.025 * (len(values) - 1))]
        hi = values[int(0.975 * (len(values) - 1))]
        rows.append({"metric_name": metric_name, "stat": key, "point": point.get(key), "ci_low_95": lo, "ci_high_95": hi, "n_bootstrap": len(values)})
    return rows


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    return ((row.get("feature_blocks") or {}).get("Q_e") or {})


def wrong_pair_control_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["candidate_id"] = f"{row['candidate_id']}::pobs_control::wrong_pair_evidence_control"
    out["control_type"] = "wrong_pair_evidence_control"
    out["row_role"] = "synthetic_unobservable_control"
    out["obs_label"] = 0
    out["rel_label"] = None
    out["decision_label"] = "abstain"
    out["feature_blocks"] = {
        "Q_e": {
            "geometry_observable": True,
            "mesh_or_semseg_available": True,
            "object_obb_available": True,
            "geometry_quality_flag": "wrong_pair_evidence",
            "synthetic_missing_evidence_control": True,
            "Q_e_safe": {
                "raw_geometry_available": True,
                "object_pair_feature_coverage": 0.15,
                "raw_geometry_feature_count": 4,
                "mesh_or_point_availability": "wrong_pair_evidence",
            },
            "Q_e_observability": {
                "q_e_state_code": 0.05,
                "q_e_state_sufficient": 0,
                "q_e_state_limited": 1,
                "q_e_state_uncertain": 0,
                "view_pair_mismatch_flag": 1,
                "subject_has_obb": 1,
                "object_has_obb": 1,
                "multiview_packet_possible": 0,
                "point_pair_crop_possible": 0,
            },
        }
    }
    return out


def file_count_for_instance(files: list[Path], instance_id: Any) -> dict[str, int]:
    try:
        target = int(instance_id)
    except (TypeError, ValueError):
        return {"jpg": 0, "crop_jpg": 0, "view_jpg": 0, "npy": 0}
    counts = {"jpg": 0, "crop_jpg": 0, "view_jpg": 0, "npy": 0}
    for file in files:
        match = INSTANCE_RE.search(file.name)
        if not match or int(match.group(1)) != target:
            continue
        if file.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            counts["jpg"] += 1
            if "croped" in file.name or "cropped" in file.name:
                counts["crop_jpg"] += 1
            else:
                counts["view_jpg"] += 1
        elif file.suffix.lower() == ".npy":
            counts["npy"] += 1
    return counts


def scan_asset_cache(scan_root: Path, scan_ids: list[str]) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    for scan_id in sorted(set(str(scan_id) for scan_id in scan_ids if scan_id not in (None, "", "None"))):
        scan_dir = scan_root / scan_id
        mv_dir = scan_dir / "multi_view"
        files = list(mv_dir.iterdir()) if mv_dir.exists() else []
        mesh_files = [p for p in scan_dir.iterdir()] if scan_dir.exists() else []
        mesh_count = sum(1 for p in mesh_files if p.suffix.lower() in {".ply", ".obj"})
        cache[scan_id] = {
            "scan_exists": scan_dir.exists(),
            "multi_view_exists": mv_dir.exists(),
            "multi_view_file_count": len(files),
            "mesh_file_count": mesh_count,
            "files": files,
        }
    return cache


def visual_mesh_observability_audit(rows: list[dict[str, Any]], scan_root: Path) -> list[dict[str, Any]]:
    observed = [row for row in rows if row.get("eval_split") == EVAL_SPLIT and row.get("control_type") == "observed_original"]
    cache = scan_asset_cache(scan_root, [str(row.get("scan_id")) for row in observed])
    audit_rows: list[dict[str, Any]] = []
    for row in observed:
        scan_id = str(row.get("scan_id"))
        entry = cache.get(scan_id, {"scan_exists": False, "multi_view_exists": False, "multi_view_file_count": 0, "mesh_file_count": 0, "files": []})
        subject_counts = file_count_for_instance(entry["files"], row.get("subject_id"))
        object_counts = file_count_for_instance(entry["files"], row.get("object_id"))
        q = q_block(row)
        q_safe = q.get("Q_e_safe", {}) if isinstance(q.get("Q_e_safe"), dict) else {}
        raw_available = bool(q_safe.get("raw_geometry_available", q.get("geometry_observable", False)))
        min_jpg = min(subject_counts["jpg"], object_counts["jpg"])
        min_crop = min(subject_counts["crop_jpg"], object_counts["crop_jpg"])
        if not entry["scan_exists"] or not entry["multi_view_exists"] or not raw_available:
            label = "unobservable"
        elif min_jpg == 0:
            label = "unobservable"
        elif min_jpg >= 2 and min_crop >= 1:
            label = "observable"
        else:
            label = "ambiguous"
        audit_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "route_family": row.get("route_family"),
                "predicate_label": row.get("predicate_label"),
                "scan_id": scan_id,
                "subject_id": row.get("subject_id"),
                "object_id": row.get("object_id"),
                "scan_exists": entry["scan_exists"],
                "multi_view_exists": entry["multi_view_exists"],
                "multi_view_file_count": entry["multi_view_file_count"],
                "mesh_file_count": entry["mesh_file_count"],
                "subject_jpg_count": subject_counts["jpg"],
                "object_jpg_count": object_counts["jpg"],
                "subject_crop_jpg_count": subject_counts["crop_jpg"],
                "object_crop_jpg_count": object_counts["crop_jpg"],
                "raw_geometry_available": raw_available,
                "asset_observability_label": label,
                "asset_observability_label_source": "codex_visual_mesh_file_audit_from_3rscan_multiview_and_scan_assets",
            }
        )
    return audit_rows


def control_metrics(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_control: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_control[str(row["control_type"])].append(row)
    observed = by_control.get("observed_original", [])
    observed_median = median([row["p_obs_calibrated"] for row in observed])
    rows: list[dict[str, Any]] = []
    for control, bucket in sorted(by_control.items()):
        scores = [row["p_obs_calibrated"] for row in bucket]
        rows.append(
            {
                "control_type": control,
                "rows": len(bucket),
                "median_p_obs_calibrated": median(scores),
                "delta_vs_observed_median": median(scores) - observed_median,
                "abstain_rate": sum(1 for row in bucket if row["pred_decision_calibrated"] == "abstain") / max(len(bucket), 1),
            }
        )
    return rows


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def route_connection_rows(records: list[dict[str, Any]], audit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_route: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        if row.get("control_type") == "observed_original":
            by_route[str(row.get("route_family"))].append(row)
    audit_by_route = Counter(row["route_family"] for row in audit_rows)
    out: list[dict[str, Any]] = []
    for route in sorted(by_route):
        bucket = by_route[route]
        out.append(
            {
                "route_family": route,
                "rows": len(bucket),
                "median_p_obs_calibrated": median([row["p_obs_calibrated"] for row in bucket]),
                "accept_rows": sum(1 for row in bucket if row["decision_label"] == "accept"),
                "reject_rows": sum(1 for row in bucket if row["decision_label"] == "reject"),
                "asset_audit_rows": audit_by_route.get(route, 0),
                "failure_route_connection": "support/contact hard route" if route == "support_contact" else "non-failure-control route",
            }
        )
    for missing_route in ["attachment_like", "containment"]:
        out.append(
            {
                "route_family": missing_route,
                "rows": 0,
                "median_p_obs_calibrated": "",
                "accept_rows": 0,
                "reject_rows": 0,
                "asset_audit_rows": 0,
                "failure_route_connection": "not materialized in current p_obs/p_rel runtime; empirical claim blocked until route rows exist",
            }
        )
    return out


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    materialization_dir = args.materialization_dir if args.materialization_dir.is_absolute() else repo_root / args.materialization_dir
    schema_audit_dir = args.schema_audit_dir if args.schema_audit_dir.is_absolute() else repo_root / args.schema_audit_dir
    scan_root = args.scan_root if args.scan_root.is_absolute() else repo_root / args.scan_root
    out = args.out if args.out.is_absolute() else repo_root / args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    audit = read_json(schema_audit_dir / "summary.json")
    if audit.get("validation_errors") not in (0, []):
        errors.append({"error_type": "schema_audit_validation_errors", "actual": audit.get("validation_errors")})

    rows = join_views(materialization_dir)
    train = [row for row in rows if row.get("eval_split") == TRAIN_SPLIT]
    calib = [row for row in rows if row.get("eval_split") == CALIB_SPLIT]
    eval_rows = [row for row in rows if row.get("eval_split") == EVAL_SPLIT]
    pobs_train = [dict(row, target_y=int(row["obs_label"])) for row in train]
    pobs_calib = calib
    pobs_eval = eval_rows + [wrong_pair_control_row(row) for row in eval_rows if row.get("control_type") == "observed_original"]
    prel_train = [dict(row, target_y=int(row["rel_label"])) for row in train if row["obs_label"] == 1 and row.get("rel_label") is not None]
    prel_calib = [row for row in calib if row["obs_label"] == 1 and row.get("rel_label") is not None]
    prel_eval = [row for row in eval_rows if row["obs_label"] == 1 and row.get("rel_label") is not None]

    if not pobs_train or not pobs_calib or not pobs_eval:
        errors.append({"error_type": "missing_pobs_split", "train": len(pobs_train), "calib": len(pobs_calib), "eval": len(pobs_eval)})
    if not prel_train or not prel_calib or not prel_eval:
        errors.append({"error_type": "missing_prel_split", "train": len(prel_train), "calib": len(prel_calib), "eval": len(prel_eval)})

    pobs_model, pobs_prior, pobs_fit = fit_model(pobs_train, pobs_feature_fn, args.epochs, args.lr, args.l2)
    prel_model, prel_prior, prel_fit = fit_model(prel_train, prel_feature_fn, args.epochs, args.lr, args.l2)

    pobs_calib_scores_raw = [predict_one(pobs_model, pobs_prior, row, pobs_feature_fn) for row in pobs_calib]
    pobs_calib_labels = [int(row["obs_label"]) for row in pobs_calib]
    pobs_calibrator, pobs_calibration_candidates = select_calibrator(pobs_calib_labels, pobs_calib_scores_raw)

    prel_calib_scores_raw = [predict_one(prel_model, prel_prior, row, prel_feature_fn) for row in prel_calib]
    prel_calib_labels = [int(row["rel_label"]) for row in prel_calib]
    prel_calibrator, prel_calibration_candidates = select_calibrator(prel_calib_labels, prel_calib_scores_raw)

    pobs_eval_scores_raw = [predict_one(pobs_model, pobs_prior, row, pobs_feature_fn) for row in pobs_eval]
    pobs_eval_scores_cal = pobs_calibrator.transform(pobs_eval_scores_raw)
    pobs_eval_labels = [int(row["obs_label"]) for row in pobs_eval]

    prel_eval_scores_raw = [predict_one(prel_model, prel_prior, row, prel_feature_fn) for row in prel_eval]
    prel_eval_scores_cal = prel_calibrator.transform(prel_eval_scores_raw)
    prel_eval_labels = [int(row["rel_label"]) for row in prel_eval]
    prel_by_id = {row["candidate_id"]: (raw, cal) for row, raw, cal in zip(prel_eval, prel_eval_scores_raw, prel_eval_scores_cal)}

    eval_records: list[dict[str, Any]] = []
    for row, p_obs_raw, p_obs_cal in zip(pobs_eval, pobs_eval_scores_raw, pobs_eval_scores_cal):
        p_rel_raw, p_rel_cal = prel_by_id.get(row["candidate_id"], (prel_prior, prel_calibrator.transform_one(prel_prior)))
        eval_records.append(
            {
                "candidate_id": row["candidate_id"],
                "source_candidate_id": row.get("source_candidate_id"),
                "route_family": row.get("route_family"),
                "predicate_label": row.get("predicate_label"),
                "scan_id": row.get("scan_id"),
                "subject_id": row.get("subject_id"),
                "object_id": row.get("object_id"),
                "control_type": row.get("control_type"),
                "row_role": row.get("row_role"),
                "obs_label": int(row["obs_label"]),
                "rel_label": row.get("rel_label"),
                "decision_label": row["decision_label"],
                "p_obs_raw": p_obs_raw,
                "p_obs_calibrated": p_obs_cal,
                "p_rel_raw": p_rel_raw,
                "p_rel_calibrated": p_rel_cal,
                "pred_decision_calibrated": decision_pred(p_obs_cal, p_rel_cal),
            }
        )

    pobs_raw_metric = metric_row("official_validation_all_plus_wrong_pair_control", "p_obs_raw", pobs_eval_labels, pobs_eval_scores_raw)
    pobs_cal_metric = metric_row("official_validation_all_plus_wrong_pair_control", "p_obs_calibrated", pobs_eval_labels, pobs_eval_scores_cal)
    prel_raw_metric = metric_row("official_validation_observable", "p_rel_raw", prel_eval_labels, prel_eval_scores_raw)
    prel_cal_metric = metric_row("official_validation_observable", "p_rel_calibrated", prel_eval_labels, prel_eval_scores_cal)
    decision_metric = multiclass_metrics([row["decision_label"] for row in eval_records], [row["pred_decision_calibrated"] for row in eval_records])
    decision_metric.update({"scope": "official_validation_all_plus_wrong_pair_control", "metric_name": "accept_reject_abstain_calibrated"})
    curve = risk_coverage_rows(eval_records)
    audit_rows = visual_mesh_observability_audit(eval_rows, scan_root)
    audit_label_by_id = {row["candidate_id"]: row for row in audit_rows}
    observed_eval_records = [row for row in eval_records if row["control_type"] == "observed_original"]
    audit_eval_pairs = [
        (audit_label_by_id[row["candidate_id"]], row)
        for row in observed_eval_records
        if row["candidate_id"] in audit_label_by_id and audit_label_by_id[row["candidate_id"]]["asset_observability_label"] != "ambiguous"
    ]
    audit_labels = [1 if audit["asset_observability_label"] == "observable" else 0 for audit, _ in audit_eval_pairs]
    audit_scores = [row["p_obs_calibrated"] for _, row in audit_eval_pairs]
    audit_metric = metric_row("official_validation_observed_asset_audit_non_ambiguous", "p_obs_vs_asset_observability", audit_labels, audit_scores) if len(set(audit_labels)) == 2 else {
        "scope": "official_validation_observed_asset_audit_non_ambiguous",
        "metric_name": "p_obs_vs_asset_observability",
        "rows": len(audit_labels),
        "positive": sum(audit_labels),
        "negative": len(audit_labels) - sum(audit_labels),
        "auroc": "",
        "ECE_10": ece(audit_labels, audit_scores) if audit_labels else "",
        "Brier": brier(audit_labels, audit_scores) if audit_labels else "",
        "NLL": nll(audit_labels, audit_scores) if audit_labels else "",
        "note": "AUROC undefined because asset-audit labels have a single class",
    }

    write_csv(out / "calibrator_selection.csv", [
        {"target": "p_obs", "selected_calibrator": pobs_calibrator.name, **row} for row in pobs_calibration_candidates
    ] + [
        {"target": "p_rel", "selected_calibrator": prel_calibrator.name, **row} for row in prel_calibration_candidates
    ])
    write_csv(out / "calibration_metrics.csv", [pobs_raw_metric, pobs_cal_metric, prel_raw_metric, prel_cal_metric, audit_metric])
    write_csv(out / "selective_metrics.csv", [decision_metric, {"metric_name": "AURC", "scope": "official_validation_all_plus_wrong_pair_control", "AURC": aurc(curve)}])
    write_csv(out / "risk_coverage_curve.csv", curve)
    write_csv(out / "missing_evidence_control_metrics.csv", control_metrics(eval_records))
    write_csv(out / "reliability_diagram.csv", reliability_diagram(prel_eval_labels, prel_eval_scores_cal, "official_validation_observable", "p_rel_calibrated") + reliability_diagram(pobs_eval_labels, pobs_eval_scores_cal, "official_validation_all_plus_wrong_pair_control", "p_obs_calibrated"))
    write_csv(out / "bootstrap_ci.csv", bootstrap_ci(prel_eval_labels, prel_eval_scores_cal, "p_rel_calibrated") + bootstrap_ci(pobs_eval_labels, pobs_eval_scores_cal, "p_obs_calibrated"))
    write_csv(out / "observability_asset_audit_labels.csv", audit_rows)
    write_csv(out / "failure_route_connection.csv", route_connection_rows(eval_records, audit_rows))
    write_jsonl(out / "prediction_scores.jsonl", eval_records)
    write_jsonl(out / "validation_errors.jsonl", errors)

    audit_counts = Counter(row["asset_observability_label"] for row in audit_rows)
    pass_checks = {
        "asset_observability_labels_created": len(audit_rows) > 0,
        "asset_observability_has_negative_or_ambiguous": audit_counts.get("unobservable", 0) + audit_counts.get("ambiguous", 0) > 0,
        "p_obs_ece_le_0_10": float(pobs_cal_metric.get("ECE_10") or 1.0) <= 0.10,
        "p_rel_ece_le_0_10": float(prel_cal_metric.get("ECE_10") or 1.0) <= 0.10,
        "p_rel_auroc_ge_0_70": float(prel_cal_metric.get("auroc") or 0.0) >= 0.70,
        "decision_macro_f1_ge_0_70": float(decision_metric.get("macro_F1") or 0.0) >= 0.70,
        "missing_controls_abstain_ge_0_90": all(
            float(row["abstain_rate"]) >= 0.90 for row in control_metrics(eval_records) if row["control_type"] != "observed_original"
        ),
        "attachment_containment_rows_present": any(row.get("route_family") in {"attachment_like", "containment"} for row in eval_rows),
    }
    calibrated_quantitative_claim_pass = (
        pass_checks["asset_observability_labels_created"]
        and pass_checks["asset_observability_has_negative_or_ambiguous"]
        and pass_checks["p_obs_ece_le_0_10"]
        and pass_checks["p_rel_ece_le_0_10"]
        and pass_checks["p_rel_auroc_ge_0_70"]
        and pass_checks["decision_macro_f1_ge_0_70"]
        and pass_checks["missing_controls_abstain_ge_0_90"]
        and pass_checks["attachment_containment_rows_present"]
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "row_counts": {
            "pobs_train": len(pobs_train),
            "pobs_calib": len(pobs_calib),
            "pobs_eval_with_wrong_pair": len(pobs_eval),
            "prel_train": len(prel_train),
            "prel_calib": len(prel_calib),
            "prel_eval": len(prel_eval),
            "asset_audit_rows": len(audit_rows),
        },
        "selected_calibrators": {
            "p_obs": {"name": pobs_calibrator.name, "params": pobs_calibrator.params},
            "p_rel": {"name": prel_calibrator.name, "params": prel_calibrator.params},
        },
        "primary_metrics": {
            "p_obs_raw_ECE_10": pobs_raw_metric.get("ECE_10"),
            "p_obs_calibrated_ECE_10": pobs_cal_metric.get("ECE_10"),
            "p_rel_raw_ECE_10": prel_raw_metric.get("ECE_10"),
            "p_rel_calibrated_ECE_10": prel_cal_metric.get("ECE_10"),
            "p_rel_calibrated_AUROC": prel_cal_metric.get("auroc"),
            "decision_macro_F1_calibrated": decision_metric.get("macro_F1"),
            "AURC": aurc(curve),
        },
        "asset_observability_label_counts": dict(sorted(audit_counts.items())),
        "pass_checks": pass_checks,
        "calibrated_quantitative_claim_pass": calibrated_quantitative_claim_pass,
        "claim_boundary": {
            "official_test_used": False,
            "calibration_split": CALIB_SPLIT,
            "calibration_selected_without_official_validation_tuning": True,
            "asset_audited_observability_labels_used": True,
            "human_observability_labels_used": False,
            "synthetic_missing_evidence_controls_still_used": True,
            "attachment_containment_empirical_rows_available": pass_checks["attachment_containment_rows_present"],
            "pobs_prel_calibrated_quantitative_result_claim_allowed": calibrated_quantitative_claim_pass,
        },
        "validation_errors": len(errors),
        "next_todo": "compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner",
    }
    write_json(out / "summary.json", summary)
    write_json(out / "gate_decision.json", summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
