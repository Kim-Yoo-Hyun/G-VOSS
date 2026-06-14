#!/usr/bin/env python3
"""Lock relative-lateral policy/calibration provenance on train/dev only.

This gate applies the frozen `relative_lateral` geometry policy to train/dev
GT positives and left/right label-flip counterfactuals. It does not read source
predictions, does not run VL-SAT/Open3DSG metrics, and does not update the paper
claim.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from audit_relative_horizontal_coordinate import (
    FrameSpec,
    evaluate_row_with_frame,
    load_scan_geometries,
    pair_geometry,
)


SCHEMA_VERSION = "h001_relative_lateral_train_dev_policy_lock_v1"
STATUS_READY = "relative_lateral_train_dev_policy_lock_ready_no_source_metrics"
STATUS_CAVEATED = "relative_lateral_train_dev_policy_lock_ready_with_caveats_no_source_metrics"
TARGET_LABELS = ("left", "right")
INVERSE_LABEL = {"left": "right", "right": "left"}
DEFAULT_POLICY_DIR = Path("archive/experiments/H001_geom_reliability/sources/relative_lateral/policy_freeze")
DEFAULT_OUT = Path("archive/experiments/H001_geom_reliability/sources/relative_lateral/train_dev_policy_lock")
DEFAULT_TRAIN_JSON = Path("local_dataset/3DSSG_subset/relationships_train.json")
DEFAULT_DATASET_ROOT = Path("local_dataset")
DEFAULT_TRAIN_SCANS = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/subset/h001_calib_pilot/train_scans.txt"
)
DEFAULT_DEV_SCANS = Path(
    "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/subset/h001_calib_pilot/dev_scans.txt"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument("--train-json", type=Path, default=DEFAULT_TRAIN_JSON)
    parser.add_argument("--train-scans", type=Path, default=DEFAULT_TRAIN_SCANS)
    parser.add_argument("--dev-scans", type=Path, default=DEFAULT_DEV_SCANS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_scan_set(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def sigmoid(value: float) -> float:
    value = max(-60.0, min(60.0, value))
    return 1.0 / (1.0 + math.exp(-value))


def load_train_dev_rows(
    train_json: Path,
    train_scans: set[str],
    dev_scans: set[str],
) -> list[dict[str, Any]]:
    payload = read_json(train_json)
    rows: list[dict[str, Any]] = []
    for entry_idx, entry in enumerate(payload.get("scans", [])):
        scan_id = str(entry.get("scan"))
        if scan_id in train_scans:
            split = "train"
        elif scan_id in dev_scans:
            split = "dev"
        else:
            continue
        objects = entry.get("objects", {}) if isinstance(entry.get("objects"), dict) else {}
        subset_split_id = int(entry.get("split", entry_idx))
        for relation_idx, relation in enumerate(entry.get("relationships", [])):
            if len(relation) < 4:
                continue
            label = str(relation[3])
            if label not in TARGET_LABELS:
                continue
            subject_id = int(relation[0])
            object_id = int(relation[1])
            base = {
                "row_id": f"{scan_id}:{subset_split_id}:{relation_idx}:positive:{label}",
                "source_type": "gt_positive",
                "split": split,
                "scan_id": scan_id,
                "subset_split_id": subset_split_id,
                "relation_idx": relation_idx,
                "subject_id": subject_id,
                "object_id": object_id,
                "subject_label": objects.get(str(subject_id)),
                "object_label": objects.get(str(object_id)),
                "predicate_label": label,
                "target": 1,
                "counterfactual_from": None,
            }
            rows.append(base)
            flipped = dict(base)
            flipped_label = INVERSE_LABEL[label]
            flipped.update(
                {
                    "row_id": f"{scan_id}:{subset_split_id}:{relation_idx}:counterfactual:{flipped_label}",
                    "source_type": "label_flip_counterfactual",
                    "predicate_label": flipped_label,
                    "target": 0,
                    "counterfactual_from": label,
                }
            )
            rows.append(flipped)
    rows.sort(
        key=lambda row: (
            row["split"],
            row["scan_id"],
            int(row["subset_split_id"]),
            int(row["relation_idx"]),
            row["source_type"],
            row["predicate_label"],
        )
    )
    return rows


def selected_frame_from_policy(policy: dict[str, Any]) -> FrameSpec:
    return FrameSpec(
        name=str(policy["selected_frame"]),
        frame_family="scan_xy",
        left_axis=tuple(float(value) for value in policy["selected_left_axis"]),
        front_axis=tuple(float(value) for value in policy["orthogonal_axis_for_ambiguity_only"]),
    )


def score_decision(row: dict[str, Any], geometries: dict[int, dict[str, Any]], frame: FrameSpec) -> dict[str, Any]:
    subject = geometries.get(int(row["subject_id"]))
    obj = geometries.get(int(row["object_id"]))
    out = dict(row)
    out["policy_frame"] = frame.name
    out["left_axis"] = [round(value, 6) for value in frame.left_axis]
    out["front_axis"] = [round(value, 6) for value in frame.front_axis]
    if subject is None or obj is None:
        out.update(
            {
                "verification_status": "missing_geometry",
                "reason_codes": ["missing_subject_or_object_geometry"],
                "signed_margin": None,
                "target_projection_m": None,
                "other_projection_m": None,
                "margin_m": None,
                "ambiguity_flags": ["missing_geometry"],
            }
        )
        return out

    pair = pair_geometry(subject, obj)
    outcome = evaluate_row_with_frame(row, pair, frame)
    status_map = {
        "match": "satisfied",
        "contradiction": "violated",
        "uncertain": "uncertain",
    }
    signed_margin = None
    target_projection = finite(outcome.get("target_projection_m"))
    margin = finite(outcome.get("margin_m"))
    if target_projection is not None and margin is not None and margin > 0:
        expected_sign = 1.0 if row["predicate_label"] == "left" else -1.0
        signed_margin = expected_sign * target_projection / margin
    out.update(
        {
            "verification_status": status_map[outcome["strict_status"]],
            "sign_only_status": status_map[outcome["sign_only_status"]],
            "reason_codes": outcome["ambiguity_flags"],
            "signed_margin": signed_margin,
            "left_projection_m": outcome["left_projection_m"],
            "front_projection_m": outcome["front_projection_m"],
            "target_projection_m": outcome["target_projection_m"],
            "other_projection_m": outcome["other_projection_m"],
            "margin_m": outcome["margin_m"],
            "distance_xy": pair["distance_xy"],
            "mean_diag_xy": pair["mean_diag_xy"],
            "projected_overlap_max_ratio": pair["projected_overlap_max_ratio"],
            "ambiguity_flags": outcome["ambiguity_flags"],
        }
    )
    return out


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for split in ("train", "dev"):
        summary[split] = {}
        for source_type in ("gt_positive", "label_flip_counterfactual"):
            subset = [row for row in rows if row["split"] == split and row["source_type"] == source_type]
            counts = Counter(row["verification_status"] for row in subset)
            labels = Counter(row["predicate_label"] for row in subset)
            total = len(subset)
            strict_eligible = counts["satisfied"] + counts["violated"]
            if source_type == "gt_positive":
                strict_target = counts["satisfied"]
                lenient_target = counts["satisfied"] + counts["uncertain"]
                target_name = "positive"
            else:
                strict_target = counts["violated"]
                lenient_target = counts["violated"] + counts["uncertain"]
                target_name = "counterfactual_negative"
            summary[split][source_type] = {
                "total": total,
                "label_counts": dict(sorted(labels.items())),
                "status_counts": dict(sorted(counts.items())),
                f"{target_name}_strict_rate_total": strict_target / total if total else None,
                f"{target_name}_strict_purity_eligible": strict_target / strict_eligible if strict_eligible else None,
                f"{target_name}_lenient_rate_total": lenient_target / total if total else None,
                "strict_eligible": strict_eligible,
                "strict_eligible_share": strict_eligible / total if total else None,
                "uncertain_rate": counts["uncertain"] / total if total else None,
                "missing_geometry_rate": counts["missing_geometry"] / total if total else None,
            }
    summary["overall"] = {
        "rows": len(rows),
        "positive_rows": sum(1 for row in rows if row["source_type"] == "gt_positive"),
        "counterfactual_rows": sum(1 for row in rows if row["source_type"] == "label_flip_counterfactual"),
        "status_counts": dict(sorted(Counter(row["verification_status"] for row in rows).items())),
        "label_counts": dict(sorted(Counter(row["predicate_label"] for row in rows).items())),
    }
    return summary


def calibration_arrays(rows: list[dict[str, Any]], split: str) -> tuple[np.ndarray, np.ndarray]:
    xs: list[float] = []
    ys: list[int] = []
    for row in rows:
        if row["split"] != split:
            continue
        value = finite(row.get("signed_margin"))
        if value is None:
            continue
        xs.append(max(-10.0, min(10.0, value)))
        ys.append(int(row["target"]))
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)


def fit_logistic_calibrator(x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    if len(x) == 0 or len(set(int(v) for v in y.tolist())) < 2:
        return {"status": "not_fit_insufficient_train_classes"}
    mean = float(np.mean(x))
    std = float(np.std(x))
    if not math.isfinite(std) or std < 1e-6:
        std = 1.0
    z = (x - mean) / std
    positive_rate = min(1.0 - 1e-6, max(1e-6, float(np.mean(y))))
    weight = 0.0
    bias = math.log(positive_rate / (1.0 - positive_rate))
    lr = 0.05
    l2 = 1e-4
    for _ in range(5000):
        logits = np.clip(weight * z + bias, -60.0, 60.0)
        probs = 1.0 / (1.0 + np.exp(-logits))
        error = probs - y
        grad_w = float(np.mean(error * z) + l2 * weight)
        grad_b = float(np.mean(error))
        weight -= lr * grad_w
        bias -= lr * grad_b
    return {
        "status": "fit_train_only",
        "model_type": "univariate_logistic_signed_margin",
        "feature": "clipped_signed_margin_target_projection_over_margin",
        "clip_range": [-10.0, 10.0],
        "standardization": {"mean": mean, "std": std},
        "weight": weight,
        "bias": bias,
        "l2": l2,
        "iterations": 5000,
        "train_rows": int(len(x)),
        "train_positive_rate": positive_rate,
        "source_predictions_used": False,
    }


def predict(model: dict[str, Any], value: Any) -> float | None:
    x = finite(value)
    if x is None or model.get("status") != "fit_train_only":
        return None
    x = max(-10.0, min(10.0, x))
    mean = float(model["standardization"]["mean"])
    std = float(model["standardization"]["std"])
    z = (x - mean) / std
    return sigmoid(float(model["weight"]) * z + float(model["bias"]))


def auroc(y: list[int], p: list[float]) -> float | None:
    positives = sum(y)
    negatives = len(y) - positives
    if positives == 0 or negatives == 0:
        return None
    order = sorted(range(len(p)), key=lambda idx: p[idx])
    rank_sum = 0.0
    for rank, idx in enumerate(order, start=1):
        if y[idx] == 1:
            rank_sum += rank
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def ece_score(y: list[int], p: list[float], bins: int = 10) -> float | None:
    if not y:
        return None
    total = len(y)
    ece = 0.0
    for idx in range(bins):
        lo = idx / bins
        hi = (idx + 1) / bins
        selected = [j for j, prob in enumerate(p) if (lo <= prob < hi) or (idx == bins - 1 and prob == 1.0)]
        if not selected:
            continue
        acc = sum(y[j] for j in selected) / len(selected)
        conf = sum(p[j] for j in selected) / len(selected)
        ece += len(selected) / total * abs(acc - conf)
    return ece


def calibration_metrics(rows: list[dict[str, Any]], model: dict[str, Any], split: str) -> dict[str, Any]:
    y: list[int] = []
    p: list[float] = []
    for row in rows:
        if row["split"] != split:
            continue
        prob = predict(model, row.get("signed_margin"))
        if prob is None:
            continue
        row["p_geom_valid_train_dev_lateral"] = prob
        y.append(int(row["target"]))
        p.append(prob)
    if not y:
        return {"status": "no_rows", "rows": 0}
    eps = 1e-9
    brier = sum((prob - target) ** 2 for prob, target in zip(p, y)) / len(y)
    nll = -sum(
        target * math.log(max(eps, prob)) + (1 - target) * math.log(max(eps, 1.0 - prob))
        for prob, target in zip(p, y)
    ) / len(y)
    return {
        "status": "ready",
        "rows": len(y),
        "positive_rate": sum(y) / len(y),
        "mean_probability": sum(p) / len(p),
        "brier": brier,
        "nll": nll,
        "ece_10": ece_score(y, p, 10),
        "auroc": auroc(y, p),
    }


def build_gate(summary: dict[str, Any], model: dict[str, Any], dev_metrics: dict[str, Any]) -> dict[str, Any]:
    dev_pos = summary["dev"]["gt_positive"]
    dev_neg = summary["dev"]["label_flip_counterfactual"]
    checks = {
        "dev_positive_strict_purity_ge_0_80": (
            dev_pos["positive_strict_purity_eligible"] is not None
            and dev_pos["positive_strict_purity_eligible"] >= 0.80
        ),
        "dev_positive_lenient_rate_ge_0_80": (
            dev_pos["positive_lenient_rate_total"] is not None
            and dev_pos["positive_lenient_rate_total"] >= 0.80
        ),
        "dev_counterfactual_strict_negative_purity_ge_0_80": (
            dev_neg["counterfactual_negative_strict_purity_eligible"] is not None
            and dev_neg["counterfactual_negative_strict_purity_eligible"] >= 0.80
        ),
        "dev_counterfactual_lenient_nonsatisfied_ge_0_80": (
            dev_neg["counterfactual_negative_lenient_rate_total"] is not None
            and dev_neg["counterfactual_negative_lenient_rate_total"] >= 0.80
        ),
        "dev_left_right_label_coverage": set(dev_pos["label_counts"].keys()) == set(TARGET_LABELS),
        "train_left_right_label_coverage": set(summary["train"]["gt_positive"]["label_counts"].keys()) == set(TARGET_LABELS),
        "calibrator_fit_train_only": model.get("status") == "fit_train_only",
        "dev_calibration_eval_ready": dev_metrics.get("status") == "ready",
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "passed": not blockers,
        "checks": checks,
        "blockers": blockers,
        "threshold_basis": "operational train/dev policy-lock gates; not official benchmark thresholds and not source metric evidence",
    }


def commands_md() -> str:
    return """# Relative Lateral Train/Dev Policy Lock Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \\
  relative_lateral_train_dev_policy_lock
```

This uses train/dev GT positives and left/right label-flip counterfactuals only.
It does not read VL-SAT/Open3DSG predictions and does not update the paper
claim.
"""


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def report_md(manifest: dict[str, Any], summary: dict[str, Any], metrics: dict[str, Any]) -> str:
    rows = [
        "# Relative Lateral Train/Dev Policy Lock",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This artifact locks relative-lateral policy/calibration provenance on",
        "train/dev GT annotations only. It does not use source prediction rows,",
        "does not compute VL-SAT/Open3DSG metrics, and does not change the paper",
        "claim.",
        "",
        "## Policy Evaluation",
        "",
        "| Split | Row type | Rows | Status counts | Strict purity | Lenient rate |",
        "|---|---|---:|---|---:|---:|",
    ]
    for split in ("train", "dev"):
        for source_type in ("gt_positive", "label_flip_counterfactual"):
            item = summary[split][source_type]
            if source_type == "gt_positive":
                strict = item["positive_strict_purity_eligible"]
                lenient = item["positive_lenient_rate_total"]
            else:
                strict = item["counterfactual_negative_strict_purity_eligible"]
                lenient = item["counterfactual_negative_lenient_rate_total"]
            rows.append(
                "| "
                + " | ".join(
                    [
                        split,
                        source_type,
                        str(item["total"]),
                        "`" + json.dumps(item["status_counts"], sort_keys=True) + "`",
                        fmt(strict),
                        fmt(lenient),
                    ]
                )
                + " |"
            )
    rows.extend(
        [
            "",
            "## Calibration",
            "",
            "| Split | Rows | Brier | NLL | ECE-10 | AUROC |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for split in ("train", "dev"):
        item = metrics[split]
        rows.append(
            f"| {split} | {item.get('rows', 0)} | {fmt(item.get('brier'))} | "
            f"{fmt(item.get('nll'))} | {fmt(item.get('ece_10'))} | {fmt(item.get('auroc'))} |"
        )
    rows.extend(
        [
            "",
            "## Gate",
            "",
            f"- passed: `{str(manifest['gate']['passed']).lower()}`",
        ]
    )
    rows.extend(f"- blocker: `{blocker}`" for blocker in manifest["gate"]["blockers"])
    if manifest["gate"]["passed"]:
        next_text = [
            "If this extension is continued, the next step is a metric-free source",
            "protocol freeze for VL-SAT/Open3DSG lateral rows, followed by held-out",
            "source metrics, controls, bootstrap CI, and failure/audit evidence.",
        ]
    else:
        next_text = [
            "The dev strict policy gate did not pass. Do not run paper-facing",
            "VL-SAT/Open3DSG lateral source metrics from this artifact yet unless",
            "the result is explicitly kept as caveated appendix evidence.",
            "The next technical step is to diagnose dev strict contradictions and",
            "uncertain rows without changing the validation policy.",
        ]
    rows.extend(
        [
            "",
            "## Next",
            "",
            *next_text,
            "",
        ]
    )
    return "\n".join(rows)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = resolve(repo_root, args.dataset_root)
    policy_dir = resolve(repo_root, args.policy_dir)
    train_json = resolve(repo_root, args.train_json)
    train_scans_path = resolve(repo_root, args.train_scans)
    dev_scans_path = resolve(repo_root, args.dev_scans)
    out = resolve(repo_root, args.out)

    policy_freeze_manifest = read_json(policy_dir / "manifest.json")
    geometry_policy = read_json(policy_dir / "geometry_policy.json")
    threshold_provenance = read_json(policy_dir / "threshold_provenance.json")
    frame = selected_frame_from_policy(geometry_policy)
    train_scans = read_scan_set(train_scans_path)
    dev_scans = read_scan_set(dev_scans_path)
    base_rows = load_train_dev_rows(train_json, train_scans, dev_scans)
    scans = sorted({row["scan_id"] for row in base_rows})

    geometry_warnings: list[str] = []
    geometry_errors: list[str] = []
    geometries_by_scan: dict[str, dict[int, dict[str, Any]]] = {}
    for scan_id in scans:
        geometries, warnings, errors = load_scan_geometries(dataset_root, scan_id)
        geometries_by_scan[scan_id] = geometries
        geometry_warnings.extend(warnings[:10])
        geometry_errors.extend(errors)

    decision_rows = [score_decision(row, geometries_by_scan.get(row["scan_id"], {}), frame) for row in base_rows]
    summary = summarize_rows(decision_rows)
    train_x, train_y = calibration_arrays(decision_rows, "train")
    model = fit_logistic_calibrator(train_x, train_y)
    metrics = {
        "train": calibration_metrics(decision_rows, model, "train"),
        "dev": calibration_metrics(decision_rows, model, "dev"),
    }
    gate = build_gate(summary, model, metrics["dev"])
    status = STATUS_READY if gate["passed"] else STATUS_CAVEATED

    if gate["passed"]:
        next_gate = "relative_lateral_source_metric_protocol_freeze_before_heldout_source_metrics"
        blockers = [
            "source_metric_protocol_not_frozen",
            "relative_lateral_vlsat_open3dsg_metrics_not_run",
            "controls_not_run",
            "bootstrap_ci_not_run",
            "failure_analysis_and_visual_audit_not_run",
            "main_claim_requires_explicit_user_confirmation",
        ]
    else:
        next_gate = "relative_lateral_dev_failure_diagnosis_or_keep_as_caveated_extension"
        blockers = [
            "dev_strict_policy_gate_failed",
            "source_metrics_blocked_until_dev_strict_failure_is_diagnosed_or_claim_is_explicitly_kept_caveated",
            "main_claim_requires_explicit_user_confirmation",
        ] + gate["blockers"]

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "candidate_family": "relative_lateral",
            "labels": list(TARGET_LABELS),
            "source_predictions_used": False,
            "source_metrics_run": False,
            "paper_claim_promotion_allowed": False,
        },
        "inputs": {
            "policy_freeze_manifest": relpath(repo_root, policy_dir / "manifest.json"),
            "geometry_policy": relpath(repo_root, policy_dir / "geometry_policy.json"),
            "threshold_provenance": relpath(repo_root, policy_dir / "threshold_provenance.json"),
            "train_json": relpath(repo_root, train_json),
            "train_scans": relpath(repo_root, train_scans_path),
            "dev_scans": relpath(repo_root, dev_scans_path),
            "dataset_root": relpath(repo_root, dataset_root),
        },
        "policy": {
            "policy_name": geometry_policy["policy_name"],
            "selected_frame": geometry_policy["selected_frame"],
            "selected_left_axis": geometry_policy["selected_left_axis"],
            "orthogonal_axis_for_ambiguity_only": geometry_policy["orthogonal_axis_for_ambiguity_only"],
            "threshold_provenance": threshold_provenance,
            "policy_freeze_status": policy_freeze_manifest["status"],
            "policy_changed_after_freeze": False,
        },
        "scope": {
            "train_scan_ids": len(train_scans),
            "dev_scan_ids": len(dev_scans),
            "scans_with_lateral_rows": len(scans),
            "decision_rows": len(decision_rows),
            "positive_rows": summary["overall"]["positive_rows"],
            "counterfactual_rows": summary["overall"]["counterfactual_rows"],
            "label_counts": summary["overall"]["label_counts"],
        },
        "summary": summary,
        "calibration": {
            "model_status": model.get("status"),
            "model_type": model.get("model_type"),
            "fit_split": "train_only",
            "dev_used_for_model_selection": False,
            "source_predictions_used": False,
            "metrics": metrics,
        },
        "gate": gate,
        "geometry": {
            "errors": geometry_errors,
            "warning_sample": geometry_warnings[:50],
        },
        "next_gate": next_gate,
        "blockers": blockers,
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "policy_lock.json", {"schema_version": SCHEMA_VERSION, "summary": summary, "gate": gate})
    write_json(out / "calibration_model.json", model)
    write_json(out / "metrics.json", {"schema_version": SCHEMA_VERSION, "status": status, "metrics": metrics})
    write_jsonl(out / "rows.jsonl", decision_rows)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, summary, metrics))
    print(
        json.dumps(
            {
                "status": status,
                "out": relpath(repo_root, out),
                "decision_rows": len(decision_rows),
                "train_positive_rows": summary["train"]["gt_positive"]["total"],
                "dev_positive_rows": summary["dev"]["gt_positive"]["total"],
                "dev_positive_strict_purity": summary["dev"]["gt_positive"]["positive_strict_purity_eligible"],
                "dev_counterfactual_negative_strict_purity": summary["dev"]["label_flip_counterfactual"][
                    "counterfactual_negative_strict_purity_eligible"
                ],
                "dev_calibration_auroc": metrics["dev"].get("auroc"),
                "gate_passed": gate["passed"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
