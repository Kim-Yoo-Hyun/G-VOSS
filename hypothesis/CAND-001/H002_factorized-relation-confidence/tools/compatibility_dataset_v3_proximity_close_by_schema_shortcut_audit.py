#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for materialized close-by rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit"

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_v1"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut"
STATUS_READY = "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_ready_for_smoke_plan"
STATUS_ERROR = "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_input_errors"
NEXT_BLOCKED_TODO = "compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
NEXT_READY_TODO = "compatibility_dataset_v3_proximity_close_by_sanitized_view_smoke_plan"

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75
HIGH_RISK_AUROC = 0.95

BLOCKED_FEATURE_FRAGMENTS = (
    "label_match_status",
    "geometry_status",
    "candidate_bucket",
    "distance_bucket",
    "scan_id",
    "directed_pair_id",
    "row_key",
    "prediction_id",
    "p_geom_valid",
    "p_geom_invalid",
    "target_construction",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def value_key(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.8g}"
    return str(value)


def risk_level(accuracy: float, auroc: float | None = None) -> str:
    score = max(accuracy, auroc if auroc is not None else 0.0)
    if score >= HIGH_RISK_ACC:
        return "high"
    if score >= MEDIUM_RISK_ACC:
        return "medium"
    return "low"


def validate_input(summary: dict[str, Any], input_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "fills_labels", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["model_safe_view.jsonl", "hidden_manifest.jsonl", "quota_audit.csv", "cap_audit.csv", "schema_precheck.csv"]:
        path = input_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_input_artifact", "path": rel_path(path)})
    return errors


def binary_rows(model_rows: list[dict[str, Any]], hidden_by_id: dict[str, dict[str, Any]], subset: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in model_rows:
        if row.get("subset") != subset:
            continue
        label = row.get("targets", {}).get("C_e_label")
        if label not in (0, 1):
            continue
        rows.append({"model": row, "hidden": hidden_by_id[row["row_id"]], "label": int(label)})
    return rows


def categorical_probe(
    rows: list[dict[str, Any]],
    probe_name: str,
    feature_source: str,
    allowed_in_model: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
) -> dict[str, Any]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        groups[value_key(value_fn(row))][row["label"]] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows) if rows else 0.0
    return {
        "probe_name": probe_name,
        "probe_type": "categorical_majority",
        "feature_source": feature_source,
        "allowed_in_model": allowed_in_model,
        "rows": len(rows),
        "num_values": len(groups),
        "accuracy": round(accuracy, 6),
        "auroc": "",
        "risk_level": risk_level(accuracy),
        "interpretation": interpretation,
    }


def auc_pairwise(values: list[float], labels: list[int]) -> float | None:
    positives = [value for value, label in zip(values, labels) if label == 1]
    negatives = [value for value, label in zip(values, labels) if label == 0]
    if not positives or not negatives:
        return None
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos in positives:
        for neg in negatives:
            if pos > neg:
                wins += 1.0
            elif pos == neg:
                wins += 0.5
    auc = wins / total
    return max(auc, 1.0 - auc)


def numeric_probe(
    rows: list[dict[str, Any]],
    probe_name: str,
    feature_source: str,
    allowed_in_model: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
) -> dict[str, Any]:
    pairs: list[tuple[float, int]] = []
    missing = 0
    for row in rows:
        value = safe_float(value_fn(row))
        if value is None:
            missing += 1
            continue
        pairs.append((value, row["label"]))
    if not pairs:
        return {
            "probe_name": probe_name,
            "probe_type": "numeric_threshold",
            "feature_source": feature_source,
            "allowed_in_model": allowed_in_model,
            "rows": len(rows),
            "num_values": 0,
            "accuracy": 0.0,
            "auroc": "",
            "risk_level": "low",
            "interpretation": interpretation,
            "missing": missing,
            "best_rule": "no_numeric_values",
        }
    values = sorted(set(value for value, _ in pairs))
    thresholds = values
    best_acc = 0.0
    best_rule = ""
    for threshold in thresholds:
        for direction in ["le_positive", "ge_positive"]:
            correct = 0
            for value, label in pairs:
                pred = int(value <= threshold) if direction == "le_positive" else int(value >= threshold)
                correct += int(pred == label)
            acc = correct / len(pairs)
            if acc > best_acc:
                best_acc = acc
                best_rule = f"{direction}@{threshold:.8g}"
    auc = auc_pairwise([value for value, _ in pairs], [label for _, label in pairs])
    return {
        "probe_name": probe_name,
        "probe_type": "numeric_threshold",
        "feature_source": feature_source,
        "allowed_in_model": allowed_in_model,
        "rows": len(rows),
        "num_values": len(values),
        "accuracy": round(best_acc, 6),
        "auroc": round(auc, 6) if auc is not None else "",
        "risk_level": risk_level(best_acc, auc),
        "interpretation": interpretation,
        "missing": missing,
        "best_rule": best_rule,
    }


def schema_leakage_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    hit_count = 0
    for row in model_rows:
        text = json.dumps(row.get("feature_blocks", {}), ensure_ascii=False, sort_keys=True)
        hits = [fragment for fragment in BLOCKED_FEATURE_FRAGMENTS if fragment in text]
        if hits:
            hit_count += 1
            if len(rows) < 50:
                rows.append({"row_id": row["row_id"], "blocked_hits": ";".join(hits)})
    rows.append({"row_id": "__summary__", "blocked_hits": hit_count, "passed": hit_count == 0})
    return rows


def run_probe_suite(rows: list[dict[str, Any]], subset_name: str) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    hidden = lambda dotted: (lambda row: nested_get(row["hidden"], dotted))
    model = lambda dotted: (lambda row: nested_get(row["model"], dotted))
    for probe in [
        categorical_probe(rows, f"{subset_name}:class_pair_only", "hidden_control", False, hidden("hidden_controls.subject_object_class_pair"), "class-pair memorization risk"),
        categorical_probe(rows, f"{subset_name}:class_pair_rank", "hidden_control", False, hidden("hidden_controls.class_pair_rank_key"), "class-pair plus rank memorization risk"),
        categorical_probe(rows, f"{subset_name}:rank_band", "Z_e_safe", True, model("feature_blocks.Z_e_safe.rank_band"), "source rank shortcut"),
        categorical_probe(rows, f"{subset_name}:raw_distance_bin", "hidden_control", False, hidden("hidden_controls.raw_distance_bin"), "raw metric distance bucket shortcut"),
        categorical_probe(rows, f"{subset_name}:norm_distance_bin", "hidden_control", False, hidden("hidden_controls.norm_distance_bin"), "normalized distance bucket shortcut"),
        categorical_probe(rows, f"{subset_name}:scan_id", "hidden_control", False, hidden("identity.scan_id"), "scan memorization if leaked"),
        categorical_probe(rows, f"{subset_name}:directed_pair_id", "hidden_control", False, hidden("identity.directed_pair_id"), "endpoint-pair memorization if leaked"),
        numeric_probe(rows, f"{subset_name}:distance_xy", "G_e", True, model("feature_blocks.G_e.distance_xy"), "raw distance baseline"),
        numeric_probe(rows, f"{subset_name}:distance_3d", "G_e", True, model("feature_blocks.G_e.distance_3d"), "raw distance baseline"),
        numeric_probe(rows, f"{subset_name}:normalized_distance_xy", "G_e", True, model("feature_blocks.G_e.normalized_distance_xy"), "normalized distance baseline"),
        numeric_probe(rows, f"{subset_name}:normalized_distance_3d", "G_e", True, model("feature_blocks.G_e.normalized_distance_3d"), "normalized distance baseline"),
        numeric_probe(rows, f"{subset_name}:projected_iou_xy", "G_e", True, model("feature_blocks.G_e.projected_iou_xy"), "overlap geometry baseline"),
        numeric_probe(rows, f"{subset_name}:semantic_score_norm", "Z_e_safe", True, model("feature_blocks.Z_e_safe.semantic_score_norm"), "source semantic score shortcut"),
        numeric_probe(rows, f"{subset_name}:p_geom_valid_rule", "hidden_baseline_only", False, hidden("hidden_controls.p_geom_valid"), "H001-style geometry-rule baseline"),
    ]:
        probes.append(probe)
    return probes


def shortcut_blockers(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    critical_names = [
        "primary_binary:normalized_distance_xy",
        "primary_binary:normalized_distance_3d",
        "primary_binary:p_geom_valid_rule",
        "primary_binary:distance_xy",
        "primary_binary:distance_3d",
    ]
    for probe in probes:
        if probe["probe_name"] in critical_names and probe["risk_level"] == "high":
            blockers.append(
                {
                    "blocker": probe["probe_name"],
                    "accuracy": probe["accuracy"],
                    "auroc": probe["auroc"],
                    "reason": "critical distance/geometry-rule baseline solves or nearly solves close-by target",
                }
            )
    return blockers


def build_report(summary: dict[str, Any], blockers: list[dict[str, Any]], top_probes: list[dict[str, Any]]) -> str:
    return f"""# H002 Proximity Close-By Schema Shortcut Audit

## Status

```text
status = {summary["status"]}
validation_errors = {summary["validation_errors"]}
critical_blockers = {summary["critical_blockers"]}
learned_smoke_allowed = {str(summary["learned_smoke_allowed"]).lower()}
next_todo = {summary["next_todo"]}
```

## Result

The materialized `close by` rows pass schema leakage checks, but learned smoke is
blocked. The target is too strongly solved by distance and rule-based geometry
baselines.

## Critical Blockers

{chr(10).join(f"- {row['blocker']}: accuracy={row['accuracy']}, auroc={row['auroc']}" for row in blockers)}

## Top Shortcut Probes

{chr(10).join(f"- {row['probe_name']}: acc={row['accuracy']}, auroc={row['auroc']}, risk={row['risk_level']}" for row in top_probes[:10])}

## Interpretation

For `close by`, the current target is valid as a diagnostic proximity-family
artifact, but not as a main H002 claim. A strong method result would need to beat
`distance_only` and `p_geom_valid_rule`; here those baselines already solve the
primary binary target. Therefore the next step is a path decision, not learned
smoke.
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary_path = args.input_dir / "summary.json"
    input_summary = read_json(input_summary_path) if input_summary_path.exists() else {}
    validation_errors = validate_input(input_summary, args.input_dir)

    if validation_errors:
        model_rows: list[dict[str, Any]] = []
        hidden_rows: list[dict[str, Any]] = []
    else:
        model_rows = read_jsonl(args.input_dir / "model_safe_view.jsonl")
        hidden_rows = read_jsonl(args.input_dir / "hidden_manifest.jsonl")

    hidden_by_id = {row["row_id"]: row for row in hidden_rows}
    if len(hidden_by_id) != len(hidden_rows):
        validation_errors.append({"error_type": "duplicate_hidden_row_id"})
    missing_hidden = [row["row_id"] for row in model_rows if row["row_id"] not in hidden_by_id]
    if missing_hidden:
        validation_errors.append({"error_type": "missing_hidden_rows", "count": len(missing_hidden)})

    schema_rows = schema_leakage_rows(model_rows)
    if schema_rows[-1].get("passed") is not True:
        validation_errors.append({"error_type": "schema_leakage_detected", "hits": schema_rows[-1].get("blocked_hits")})

    primary_rows = binary_rows(model_rows, hidden_by_id, "primary_binary") if not validation_errors else []
    raw_diag_rows = binary_rows(model_rows, hidden_by_id, "raw_distance_diagnostic") if not validation_errors else []
    combined_rows = primary_rows + raw_diag_rows
    probes = run_probe_suite(primary_rows, "primary_binary")
    probes.extend(run_probe_suite(raw_diag_rows, "raw_distance_diagnostic"))
    probes.extend(run_probe_suite(combined_rows, "combined_binary"))
    blockers = shortcut_blockers(probes)

    learned_smoke_allowed = not blockers and not validation_errors
    status = STATUS_ERROR if validation_errors else (STATUS_READY if learned_smoke_allowed else STATUS_BLOCKED)
    next_todo = NEXT_READY_TODO if learned_smoke_allowed else NEXT_BLOCKED_TODO
    top_probes = sorted(
        probes,
        key=lambda row: (
            row["risk_level"] == "high",
            row["accuracy"],
            float(row["auroc"]) if row["auroc"] != "" else 0.0,
        ),
        reverse=True,
    )

    risk_summary = {
        "critical_blockers": blockers,
        "learned_smoke_allowed": learned_smoke_allowed,
        "main_claim_verdict": "blocked_for_close_by_current_target" if blockers else "schema_audit_passed",
        "primary_rows": len(primary_rows),
        "raw_distance_diagnostic_rows": len(raw_diag_rows),
        "schema_leakage_passed": schema_rows[-1].get("passed") is True,
        "top_high_risk_probes": [row for row in top_probes if row["risk_level"] == "high"][:20],
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo if not validation_errors else "fix_audit_input_errors",
        "validation_errors": len(validation_errors),
        "critical_blockers": len(blockers),
        "learned_smoke_allowed": learned_smoke_allowed,
        "input_materialization_summary": rel_path(input_summary_path),
        "main_claim_verdict": risk_summary["main_claim_verdict"],
        "row_counts": {
            "model_rows": len(model_rows),
            "hidden_rows": len(hidden_rows),
            "primary_binary_rows": len(primary_rows),
            "raw_distance_diagnostic_rows": len(raw_diag_rows),
        },
        "boundary": {
            "split": "train_only_schema_shortcut_audit",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "schema_leakage": rel_path(args.output_dir / "schema_leakage.csv"),
            "shortcut_probes": rel_path(args.output_dir / "shortcut_probes.csv"),
            "risk_summary": rel_path(args.output_dir / "risk_summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "schema_leakage.csv", schema_rows)
    write_csv(args.output_dir / "shortcut_probes.csv", probes)
    write_json(args.output_dir / "risk_summary.json", risk_summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(build_report(summary, blockers, top_probes), encoding="utf-8")


if __name__ == "__main__":
    main()
