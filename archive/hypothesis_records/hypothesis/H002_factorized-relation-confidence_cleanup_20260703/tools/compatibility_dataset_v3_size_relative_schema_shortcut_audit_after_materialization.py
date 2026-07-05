#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for size-relative materialized rows."""

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

DEFAULT_INPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_after_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization"

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_size_relative_candidate_materialization_after_plan_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_v1"
SMOKE_READY_SCHEMA = "h002_size_relative_smoke_ready_view_v1"
STATUS_READY = "h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_ready_for_smoke_plan"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_blocked_shortcut_risk"
STATUS_ERROR = "h002_compatibility_dataset_v3_size_relative_schema_shortcut_audit_after_materialization_input_errors"
NEXT_READY = "compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit"
NEXT_BLOCKED = "compatibility_dataset_v3_size_relative_path_decision_after_schema_shortcut_audit"

EXPECTED_PRIMARY_ROWS = 2400
EXPECTED_PRIMARY_GROUPS = 1200
HIGH_RISK = 0.95
MEDIUM_RISK = 0.75
MAX_ALLOWED_SINGLE_FEATURE_RISK = 0.60

ALLOWED_FEATURE_PATHS = {
    "feature_blocks",
    "feature_blocks.G_e_size",
    "feature_blocks.G_e_size.log_footprint_area_ratio_s_over_o",
    "feature_blocks.G_e_size.log_max_extent_ratio_s_over_o",
    "feature_blocks.G_e_size.log_vertical_extent_ratio_s_over_o",
    "feature_blocks.G_e_size.log_volume_ratio_s_over_o",
    "feature_blocks.T_e",
    "feature_blocks.T_e.predicate_label",
    "feature_blocks.T_e.predicate_text",
    "feature_blocks.T_e.relation_family",
}

BLOCKED_FEATURE_FRAGMENTS = (
    "anchor",
    "candidate_component",
    "class",
    "construction",
    "direction_by",
    "directed_pair",
    "gt_",
    "object_id",
    "scan_id",
    "source",
    "subgraph",
    "subject_id",
    "volume_ratio_band",
    "z_e",
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def flatten_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(flatten_paths(child, path))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        output = float(value)
    except (TypeError, ValueError):
        return None
    return output if math.isfinite(output) else None


def value_key(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def risk_level(accuracy: float, auroc: float | None = None) -> str:
    score = max(accuracy, auroc if auroc is not None else 0.0)
    if score >= HIGH_RISK:
        return "high"
    if score >= MEDIUM_RISK:
        return "medium"
    return "low"


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


def categorical_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    probe_name: str,
    source: str,
    allowed_feature: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
) -> dict[str, Any]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row, label in zip(rows, labels):
        groups[value_key(value_fn(row))][label] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows) if rows else 0.0
    return {
        "probe_name": probe_name,
        "probe_type": "categorical_majority",
        "source": source,
        "allowed_feature": allowed_feature,
        "rows": len(rows),
        "num_values": len(groups),
        "accuracy": round(accuracy, 6),
        "auroc": "",
        "risk_level": risk_level(accuracy),
        "interpretation": interpretation,
    }


def numeric_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    probe_name: str,
    source: str,
    allowed_feature: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
) -> dict[str, Any]:
    values: list[float] = []
    observed_labels: list[int] = []
    missing = 0
    for row, label in zip(rows, labels):
        value = safe_float(value_fn(row))
        if value is None:
            missing += 1
            continue
        values.append(value)
        observed_labels.append(label)
    auc = auc_pairwise(values, observed_labels)
    score = auc if auc is not None else 0.0
    return {
        "probe_name": probe_name,
        "probe_type": "numeric_auc",
        "source": source,
        "allowed_feature": allowed_feature,
        "rows": len(rows),
        "observed_values": len(values),
        "missing_values": missing,
        "accuracy": "",
        "auroc": round(auc, 6) if auc is not None else "",
        "risk_level": risk_level(0.0, score),
        "interpretation": interpretation,
    }


def validate_input(summary: dict[str, Any], input_errors: list[dict[str, Any]], input_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors_present", "actual": summary.get("validation_errors")})
    if input_errors:
        errors.append({"error_type": "input_validation_error_rows_present", "rows": len(input_errors)})
    boundary = summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "paper_evidence_allowed", "runs_new_learned_smoke", "trains_new_model", "validation_usage", "test_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in [
        "model_safe_main_view.jsonl",
        "model_safe_qe_view.jsonl",
        "hidden_manifest.jsonl",
        "group_manifest.jsonl",
        "schema_precheck.json",
    ]:
        path = input_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_input_artifact", "path": rel_path(path)})
    return errors


def feature_path_audit(model_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    counts: Counter[str] = Counter()
    violations: list[dict[str, Any]] = []
    for row in model_rows:
        for path in flatten_paths(row.get("feature_blocks", {}), "feature_blocks"):
            counts[path] += 1
            lower = path.lower()
            blocked_hits = [fragment for fragment in BLOCKED_FEATURE_FRAGMENTS if fragment in lower]
            allowed = path in ALLOWED_FEATURE_PATHS
            if not allowed or blocked_hits:
                violations.append(
                    {
                        "row_id": row.get("row_id"),
                        "feature_path": path,
                        "allowed": allowed,
                        "blocked_hits": ";".join(blocked_hits),
                    }
                )
    audit_rows = [
        {
            "feature_path": path,
            "rows": count,
            "allowed": path in ALLOWED_FEATURE_PATHS,
            "blocked_fragment_hits": ";".join(fragment for fragment in BLOCKED_FEATURE_FRAGMENTS if fragment in path.lower()),
        }
        for path, count in sorted(counts.items())
    ]
    return audit_rows, violations


def hidden_by_row_id(hidden_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["row_id"]: row for row in hidden_rows}


def primary_rows(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[int]]:
    hidden = hidden_by_row_id(hidden_rows)
    rows: list[dict[str, Any]] = []
    hidden_for_rows: list[dict[str, Any]] = []
    labels: list[int] = []
    for row in model_rows:
        if row.get("subset") != "primary_compatibility":
            continue
        label = row.get("labels", {}).get("C_e")
        if label not in (0, 1):
            continue
        rows.append(row)
        hidden_for_rows.append(hidden[row["row_id"]])
        labels.append(int(label))
    return rows, hidden_for_rows, labels


def geometry_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    g = row.get("feature_blocks", {}).get("G_e_size", {})
    return (
        value_key(g.get("log_volume_ratio_s_over_o")),
        value_key(g.get("log_max_extent_ratio_s_over_o")),
        value_key(g.get("log_footprint_area_ratio_s_over_o")),
        value_key(g.get("log_vertical_extent_ratio_s_over_o")),
    )


def build_shortcut_probes(model_rows: list[dict[str, Any]], labels: list[int]) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    probes.append(
        categorical_probe(
            model_rows,
            labels,
            "T_predicate_label_only",
            "model_safe_main_view",
            True,
            lambda row: nested_get(row, "feature_blocks.T_e.predicate_label"),
            "Semantic predicate alone should be balanced because bigger/smaller positives are symmetric.",
        )
    )
    probes.append(
        categorical_probe(
            model_rows,
            labels,
            "T_relation_family_only",
            "model_safe_main_view",
            True,
            lambda row: nested_get(row, "feature_blocks.T_e.relation_family"),
            "Relation family is constant and should be uninformative.",
        )
    )
    probes.append(
        categorical_probe(
            model_rows,
            labels,
            "G_exact_tuple_only",
            "model_safe_main_view",
            True,
            geometry_tuple,
            "Exact G_e tuple should have one positive and one negative row inside each same-G group.",
        )
    )
    for field in [
        "log_volume_ratio_s_over_o",
        "log_max_extent_ratio_s_over_o",
        "log_footprint_area_ratio_s_over_o",
        "log_vertical_extent_ratio_s_over_o",
    ]:
        probes.append(
            numeric_probe(
                model_rows,
                labels,
                f"G_single_{field}",
                "model_safe_main_view",
                True,
                lambda row, field=field: nested_get(row, f"feature_blocks.G_e_size.{field}"),
                "A single geometry ratio should be near chance under same-G predicate flip.",
            )
        )
    probes.append(
        categorical_probe(
            model_rows,
            labels,
            "TG_exact_interaction",
            "model_safe_main_view",
            True,
            lambda row: (
                nested_get(row, "feature_blocks.T_e.predicate_label"),
                geometry_tuple(row),
            ),
            "This high score is intended: compatibility should require T_e x G_e interaction.",
        )
    )
    return probes


def build_hidden_probes(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]], labels: list[int]) -> list[dict[str, Any]]:
    joined = [{"model": model, "hidden": hidden} for model, hidden in zip(model_rows, hidden_rows)]
    probes: list[dict[str, Any]] = []
    for name, fn, interpretation in [
        ("hidden_class_pair_only", lambda row: row["hidden"].get("class_pair"), "Class-pair hidden probe checks whether object semantics alone reconstruct labels."),
        ("hidden_source_predicate_only", lambda row: row["hidden"].get("source_predicate_label"), "Source predicate alone should be balanced by construction."),
        ("hidden_anchor_predicate_only", lambda row: row["hidden"].get("anchor_predicate_label"), "Anchor predicate alone should be balanced by construction."),
        ("hidden_direction_only", lambda row: row["hidden"].get("direction_by_volume"), "Geometry direction alone should be balanced because each direction has both predicates."),
        ("hidden_scan_only", lambda row: row["hidden"].get("scan_id"), "Scan id is hidden and should not be relied on."),
        ("hidden_volume_band_only", lambda row: row["hidden"].get("volume_ratio_band"), "Volume band should be uninformative in primary rows."),
        ("hidden_original_gt_anchor_flag", lambda row: row["hidden"].get("is_original_gt_anchor"), "Original/counterfactual flag is hidden construction metadata."),
        (
            "hidden_direction_x_candidate_predicate",
            lambda row: (row["hidden"].get("direction_by_volume"), row["model"].get("feature_blocks", {}).get("T_e", {}).get("predicate_label")),
            "This is an expected construction rule and must remain hidden except for audit.",
        ),
    ]:
        probes.append(categorical_probe(joined, labels, name, "hidden_manifest", False, fn, interpretation))
    return probes


def group_integrity_audit(model_rows: list[dict[str, Any]], group_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_rows:
        by_group[row["group_id"]].append(row)
    audit_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for group in group_rows:
        if group.get("subset") != "primary_compatibility":
            continue
        rows = by_group.get(group["group_id"], [])
        predicates = sorted(nested_get(row, "feature_blocks.T_e.predicate_label") for row in rows)
        labels = sorted(row.get("labels", {}).get("C_e") for row in rows)
        g_tuples = {geometry_tuple(row) for row in rows}
        passed = len(rows) == 2 and predicates == ["bigger than", "smaller than"] and labels == [0, 1] and len(g_tuples) == 1
        audit = {
            "group_id": group["group_id"],
            "rows": len(rows),
            "predicates": ";".join(str(value) for value in predicates),
            "labels": ";".join(str(value) for value in labels),
            "same_g_tuple": len(g_tuples) == 1,
            "pass": passed,
        }
        audit_rows.append(audit)
        if not passed:
            errors.append(audit)
    return audit_rows, errors


def smoke_ready_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in model_rows:
        if row.get("subset") != "primary_compatibility":
            continue
        output.append(
            {
                "schema_version": SMOKE_READY_SCHEMA,
                "dataset_name": row["dataset_name"],
                "row_id": row["row_id"],
                "group_id": row["group_id"],
                "split": "train",
                "subset": "primary_compatibility",
                "feature_blocks": row["feature_blocks"],
                "labels": {
                    "C_e": row["labels"]["C_e"],
                    "p_rel": row["labels"]["p_rel"],
                    "p_obs": row["labels"]["p_obs"],
                },
                "cv_group": row["group_id"],
                "model_use": "size_relative_smoke_ready_if_plan_accepts",
            }
        )
    return output


def validation_from_audit(
    input_errors: list[dict[str, Any]],
    model_rows: list[dict[str, Any]],
    labels: list[int],
    feature_violations: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    group_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = list(input_errors)
    if len(model_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"error_type": "unexpected_primary_model_rows", "actual": len(model_rows), "expected": EXPECTED_PRIMARY_ROWS})
    if Counter(labels) != Counter({0: 1200, 1: 1200}):
        errors.append({"error_type": "unexpected_label_balance", "actual": dict(Counter(labels))})
    if feature_violations:
        errors.append({"error_type": "feature_path_violations", "count": len(feature_violations)})
    if group_errors:
        errors.append({"error_type": "group_integrity_errors", "count": len(group_errors)})
    for row in shortcut_rows:
        if row["probe_name"] == "TG_exact_interaction":
            continue
        score = row["auroc"] if row["auroc"] != "" else row["accuracy"]
        score = float(score)
        if row["allowed_feature"] and score > MAX_ALLOWED_SINGLE_FEATURE_RISK:
            errors.append({"error_type": "allowed_single_feature_shortcut", "probe_name": row["probe_name"], "score": score})
    hidden_high = [row for row in hidden_rows if row["risk_level"] == "high"]
    # Hidden high-risk construction probes are recorded but do not block smoke if schema separation passes.
    nonconstruction_hidden_high = [
        row
        for row in hidden_high
        if row["probe_name"] not in {"hidden_direction_x_candidate_predicate", "hidden_original_gt_anchor_flag"}
    ]
    if nonconstruction_hidden_high:
        errors.append(
            {
                "error_type": "hidden_nonconstruction_shortcut_high_risk",
                "probes": [row["probe_name"] for row in nonconstruction_hidden_high],
            }
        )
    return errors


def build_report(summary: dict[str, Any], shortcut_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> str:
    def probe_line(row: dict[str, Any]) -> str:
        score = row["auroc"] if row["auroc"] != "" else row["accuracy"]
        return f"- `{row['probe_name']}`: {score} ({row['risk_level']})"

    lines = [
        "# H002 Size-Relative Schema Shortcut Audit After Materialization",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Main Shortcut Probes",
        "",
    ]
    lines.extend(probe_line(row) for row in shortcut_rows)
    lines += ["", "## Hidden Probes", ""]
    lines.extend(probe_line(row) for row in hidden_rows)
    lines += [
        "",
        "## Interpretation",
        "",
        "- Schema leakage passed if `feature_path_violations = 0`.",
        "- T-only and G-only probes should be near chance.",
        "- `TG_exact_interaction` is expected to be high; it is the intended compatibility signal.",
        "- Hidden construction probes can be high only if they remain outside model-safe features.",
        "- No learned smoke was run in this audit stage.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary_path = args.input_dir / "summary.json"
    input_summary = read_json(input_summary_path) if input_summary_path.exists() else {}
    initial_errors = validate_input(input_summary, read_jsonl(args.input_dir / "validation_errors.jsonl"), args.input_dir)

    model_rows_raw = read_jsonl(args.input_dir / "model_safe_main_view.jsonl")
    hidden_manifest_rows = read_jsonl(args.input_dir / "hidden_manifest.jsonl")
    group_manifest_rows = read_jsonl(args.input_dir / "group_manifest.jsonl")
    model_rows, hidden_rows, labels = primary_rows(model_rows_raw, hidden_manifest_rows)

    feature_audit_rows, feature_violations = feature_path_audit(model_rows)
    shortcut_rows = build_shortcut_probes(model_rows, labels)
    hidden_probe_rows = build_hidden_probes(model_rows, hidden_rows, labels)
    group_audit_rows, group_errors = group_integrity_audit(model_rows, group_manifest_rows)
    ready_rows = smoke_ready_rows(model_rows)
    validation_errors = validation_from_audit(
        initial_errors,
        model_rows,
        labels,
        feature_violations,
        shortcut_rows,
        hidden_probe_rows,
        group_errors,
    )

    if initial_errors:
        status = STATUS_ERROR
        selected_path = "blocked_by_input_validation_errors"
        next_todo = EXPECTED_INPUT_NEXT
    elif validation_errors:
        status = STATUS_BLOCKED
        selected_path = "blocked_by_schema_or_shortcut_risk"
        next_todo = NEXT_BLOCKED
    else:
        status = STATUS_READY
        selected_path = "size_relative_smoke_ready_view_ready"
        next_todo = NEXT_READY

    output_paths = {
        "feature_path_audit": args.output_dir / "feature_path_audit.csv",
        "feature_path_violations": args.output_dir / "feature_path_violations.jsonl",
        "shortcut_probe_results": args.output_dir / "shortcut_probe_results.csv",
        "hidden_shortcut_probe_results": args.output_dir / "hidden_shortcut_probe_results.csv",
        "group_integrity_audit": args.output_dir / "group_integrity_audit.csv",
        "group_integrity_errors": args.output_dir / "group_integrity_errors.jsonl",
        "smoke_ready_view": args.output_dir / "smoke_ready_view.jsonl",
        "summary": args.output_dir / "summary.json",
        "report": args.output_dir / "report.md",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "input_dir": rel_path(args.input_dir),
            "input_summary": rel_path(input_summary_path),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only_schema_shortcut_audit",
            "materializes_rows": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "counts": {
            "input_model_safe_main_rows": len(model_rows_raw),
            "primary_rows": len(model_rows),
            "primary_label_counts": {str(key): value for key, value in Counter(labels).items()},
            "feature_path_rows": len(feature_audit_rows),
            "feature_path_violations": len(feature_violations),
            "shortcut_probe_rows": len(shortcut_rows),
            "hidden_probe_rows": len(hidden_probe_rows),
            "hidden_high_risk_probes": sum(1 for row in hidden_probe_rows if row["risk_level"] == "high"),
            "group_integrity_rows": len(group_audit_rows),
            "group_integrity_errors": len(group_errors),
            "smoke_ready_rows": len(ready_rows),
        },
        "gate": {
            "allowed_single_feature_max": MAX_ALLOWED_SINGLE_FEATURE_RISK,
            "schema_leakage_pass": len(feature_violations) == 0,
            "allowed_single_feature_pass": not any(
                row["probe_name"] != "TG_exact_interaction"
                and row["allowed_feature"]
                and float(row["auroc"] if row["auroc"] != "" else row["accuracy"]) > MAX_ALLOWED_SINGLE_FEATURE_RISK
                for row in shortcut_rows
            ),
            "group_integrity_pass": len(group_errors) == 0,
            "smoke_ready": status == STATUS_READY,
        },
        "claim_boundary": {
            "learned_smoke_allowed_next": status == STATUS_READY,
            "paper_evidence_allowed_now": False,
            "size_relative_solved": False,
            "geometry_only_success_counts_as_main_claim": False,
        },
    }

    write_csv(output_paths["feature_path_audit"], feature_audit_rows)
    write_jsonl(output_paths["feature_path_violations"], feature_violations)
    write_csv(output_paths["shortcut_probe_results"], shortcut_rows)
    write_csv(output_paths["hidden_shortcut_probe_results"], hidden_probe_rows)
    write_csv(output_paths["group_integrity_audit"], group_audit_rows)
    write_jsonl(output_paths["group_integrity_errors"], group_errors)
    write_jsonl(output_paths["smoke_ready_view"], ready_rows)
    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(build_report(summary, shortcut_rows, hidden_probe_rows), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
