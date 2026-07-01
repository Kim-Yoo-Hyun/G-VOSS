#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for H002 compatibility dataset v2."""

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

DEFAULT_INPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v2_candidate_materialization"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_schema_shortcut_audit"

EXPECTED_INPUT_STATUS = "h002_compatibility_dataset_v2_candidate_materialization_ready_for_schema_shortcut_audit"
EXPECTED_INPUT_NEXT = "compatibility_dataset_v2_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_schema_shortcut_audit_v1"
SANITIZED_VIEW_SCHEMA = "h002_compatibility_dataset_v2_sanitized_model_view_v1"

STATUS_ERROR = "h002_compatibility_dataset_v2_schema_shortcut_audit_input_errors"
STATUS_REQUIRES_SANITIZED_VIEW = "h002_compatibility_dataset_v2_schema_shortcut_audit_requires_sanitized_view"
STATUS_READY = "h002_compatibility_dataset_v2_schema_shortcut_audit_ready_for_sanitized_smoke"

NEXT_TODO_BLOCKED = "compatibility_dataset_v2_sanitized_view_smoke_plan"
NEXT_TODO_READY = "compatibility_dataset_v2_sanitized_view_smoke"

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

BLOCKED_G_FEATURE_FRAGMENTS = (
    "predicate",
    "family",
    "source",
    "rank",
    "label",
    "hidden",
    "status",
    "bucket",
    "target",
    "semantic",
    "p_geom",
    "queue",
    "machine",
    "match",
)

UNSAFE_FULL_VIEW_FIELDS = [
    "row_role",
    "counterfactual_axis.counterfactual_type",
    "hidden_control.generated",
    "hidden_control.counterfactual_type",
    "G_e.geometry_source",
    "Q_e.coverage_features.generated_counterfactual",
    "Q_e.evidence_conflict_flag",
    "geometry_status_baseline",
    "relation_source",
]


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


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def compatibility_label(row: dict[str, Any]) -> int:
    return 1 if row.get("counterfactual_axis", {}).get("compatibility_label") == "positive" else 0


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = row
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def value_key(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None or value == "":
        return "missing"
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.8g}"
    return str(value)


def risk_level(accuracy: float) -> str:
    if accuracy >= HIGH_RISK_ACC:
        return "high"
    if accuracy >= MEDIUM_RISK_ACC:
        return "medium"
    return "low"


def categorical_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    probe_name: str,
    source: str,
    allowed_model_input: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
) -> dict[str, Any]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row, label in zip(rows, labels):
        groups[value_key(value_fn(row))][label] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows) if rows else 0.0
    majority_by_value = {
        key: {
            "rows": sum(counter.values()),
            "positive": counter[1],
            "negative": counter[0],
            "majority_label": "positive" if counter[1] >= counter[0] else "negative",
        }
        for key, counter in sorted(groups.items())
    }
    return {
        "probe_name": probe_name,
        "source": source,
        "allowed_model_input": allowed_model_input,
        "probe_type": "categorical_majority",
        "accuracy": round(accuracy, 6),
        "risk_level": risk_level(accuracy),
        "num_values": len(groups),
        "best_rule": "per_value_majority",
        "interpretation": interpretation,
        "majority_by_value": majority_by_value,
    }


def best_threshold_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    probe_name: str,
    feature_name: str,
    value_fn: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    pairs: list[tuple[float, int]] = []
    missing = 0
    for row, label in zip(rows, labels):
        value = safe_float(value_fn(row))
        if value is None:
            missing += 1
            continue
        pairs.append((value, label))
    if not pairs:
        return {
            "probe_name": probe_name,
            "source": "G_e_numeric",
            "allowed_model_input": True,
            "probe_type": "numeric_threshold",
            "accuracy": 0.0,
            "risk_level": "low",
            "num_values": 0,
            "missing": missing,
            "best_rule": "no_numeric_values",
            "interpretation": "No usable numeric values.",
        }
    values = sorted({value for value, _ in pairs})
    thresholds: list[float] = []
    if len(values) == 1:
        thresholds = values
    else:
        thresholds.append(values[0] - 1e-9)
        thresholds.extend((left + right) / 2.0 for left, right in zip(values, values[1:]))
        thresholds.append(values[-1] + 1e-9)
    best_acc = -1.0
    best_rule = ""
    for threshold in thresholds:
        for direction in ("le_positive", "gt_positive"):
            correct = 0
            for value, label in pairs:
                pred = 1 if value <= threshold else 0
                if direction == "gt_positive":
                    pred = 1 - pred
                if pred == label:
                    correct += 1
            acc = correct / len(pairs)
            if acc > best_acc:
                best_acc = acc
                best_rule = f"{direction}@{threshold:.8g}"
    return {
        "probe_name": probe_name,
        "source": "G_e_numeric",
        "allowed_model_input": True,
        "probe_type": "numeric_threshold",
        "accuracy": round(best_acc, 6),
        "risk_level": risk_level(best_acc),
        "num_values": len(values),
        "missing": missing,
        "best_rule": best_rule,
        "interpretation": (
            "High accuracy here can be intended geometric counterfactual signal, not schema leakage. "
            "It becomes leakage only if the feature encodes construction metadata rather than geometry."
        ),
    }


def compact_probe_row(probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_name": probe["probe_name"],
        "source": probe["source"],
        "allowed_model_input": probe["allowed_model_input"],
        "probe_type": probe["probe_type"],
        "accuracy": probe["accuracy"],
        "risk_level": probe["risk_level"],
        "num_values": probe.get("num_values"),
        "missing": probe.get("missing"),
        "best_rule": probe.get("best_rule"),
        "interpretation": probe["interpretation"],
    }


def schema_audit(rows: list[dict[str, Any]], materialization_schema: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    c_view_keys = Counter()
    model_view_keys = Counter()
    unsafe_hits = Counter()

    for row in rows:
        row_id = row.get("row_id")
        c_view = row.get("model_views", {}).get("compatibility_main", {})
        for key in c_view:
            c_view_keys[key] += 1
        for view_name, view in row.get("model_views", {}).items():
            if isinstance(view, dict):
                for key in view:
                    model_view_keys[f"{view_name}.{key}"] += 1
        if set(c_view) != {"T_e", "G_e"}:
            errors.append({"error_type": "compatibility_main_not_exactly_T_and_G", "row_id": row_id, "keys": sorted(c_view)})
        if "Z_e" in c_view:
            errors.append({"error_type": "z_e_in_compatibility_main", "row_id": row_id})
        for key in row.get("G_e", {}).get("geometry_features", {}):
            lowered = str(key).lower()
            hit = [fragment for fragment in BLOCKED_G_FEATURE_FRAGMENTS if fragment in lowered]
            if hit:
                errors.append({"error_type": "blocked_g_feature_key", "row_id": row_id, "feature": key, "fragments": hit})
        if row.get("G_e", {}).get("geometry_source"):
            unsafe_hits["G_e.geometry_source"] += 1
        if nested_get(row, "Q_e.coverage_features.generated_counterfactual") is not None:
            unsafe_hits["Q_e.coverage_features.generated_counterfactual"] += 1
        if nested_get(row, "Q_e.evidence_conflict_flag") is not None:
            unsafe_hits["Q_e.evidence_conflict_flag"] += 1

    declared_safe_views = materialization_schema.get("model_safe_views", [])
    if "full_factorized" in declared_safe_views:
        warnings.append(
            {
                "warning_type": "declared_full_factorized_view_not_safe_without_sanitization",
                "reason": "Q_e and G_e metadata include generated-counterfactual construction fields.",
            }
        )
    if "obs_head" in declared_safe_views:
        warnings.append(
            {
                "warning_type": "declared_obs_head_not_safe_for_generated_counterfactual_dataset",
                "reason": "Q_e.generated_counterfactual and evidence_conflict_flag directly encode negative construction.",
            }
        )

    return {
        "schema_errors": errors,
        "schema_warnings": warnings,
        "compatibility_main_keys": dict(c_view_keys),
        "model_view_keys": dict(model_view_keys),
        "unsafe_metadata_hits": dict(unsafe_hits),
        "blocked_full_view_fields": UNSAFE_FULL_VIEW_FIELDS,
        "compatibility_main_exact_TG": not errors,
    }


def sanitize_q(row: dict[str, Any]) -> dict[str, Any]:
    q = row.get("Q_e", {})
    coverage = dict(q.get("coverage_features", {}))
    coverage.pop("generated_counterfactual", None)
    return {
        "asset_tier": q.get("asset_tier"),
        "coverage_features": coverage,
        "missing_geometry_flag": q.get("missing_geometry_flag"),
        "low_coverage_flag": q.get("low_coverage_flag"),
        "unsupported_family_flag": q.get("unsupported_family_flag"),
        "raw_feature_missing_count": q.get("raw_feature_missing_count"),
        "geometry_available": q.get("geometry_available"),
        "geometry_checkable": q.get("geometry_checkable"),
    }


def sanitized_model_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        g_numeric = dict(row.get("G_e", {}).get("geometry_features", {}))
        t_block = row.get("T_e", {})
        z_block = row.get("Z_e", {})
        q_sanitized = sanitize_q(row)
        out.append(
            {
                "schema_version": SANITIZED_VIEW_SCHEMA,
                "row_id": row.get("row_id"),
                "group_id": row.get("group_id"),
                "split": row.get("split"),
                "y_compatibility": compatibility_label(row),
                "T_e": t_block,
                "Z_e": z_block,
                "G_e_numeric": {
                    "geometry_features": g_numeric,
                    "geometry_feature_mask": dict(row.get("G_e", {}).get("geometry_feature_mask", {})),
                    "geometry_feature_units": dict(row.get("G_e", {}).get("geometry_feature_units", {})),
                    "geometry_normalization": row.get("G_e", {}).get("geometry_normalization"),
                },
                "Q_e_sanitized": q_sanitized,
                "model_views": {
                    "source_only": {"Z_e": z_block},
                    "semantic_content_only": {"T_e": t_block},
                    "semantic_source": {"T_e": t_block, "Z_e": z_block},
                    "geometry_numeric_only": {"G_e_numeric": g_numeric},
                    "compatibility_TG_numeric": {"T_e": t_block, "G_e_numeric": g_numeric},
                    "factorized_sanitized": {
                        "T_e": t_block,
                        "Z_e": z_block,
                        "G_e_numeric": g_numeric,
                        "Q_e_sanitized": q_sanitized,
                    },
                },
                "audit_reference": {
                    "hidden_control_available_in_source_row": True,
                    "construction_fields_removed_from_model_view": True,
                },
            }
        )
    return out


def baseline_source_score_bin(row: dict[str, Any]) -> str:
    value = safe_float(row.get("Z_e", {}).get("source_score_normalized"))
    if value is None:
        return "missing"
    if value >= 0.95:
        return "score_ge_0.95"
    if value >= 0.90:
        return "score_0.90_0.95"
    if value >= 0.80:
        return "score_0.80_0.90"
    if value >= 0.60:
        return "score_0.60_0.80"
    return "score_lt_0.60"


def run_probes(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = [compatibility_label(row) for row in rows]
    probes: list[dict[str, Any]] = [
        categorical_probe(
            rows,
            labels,
            "hidden_row_role",
            "hidden_control",
            False,
            lambda row: row.get("row_role"),
            "Row role is anchor_positive vs counterfactual_negative; it must never be model input.",
        ),
        categorical_probe(
            rows,
            labels,
            "hidden_counterfactual_type",
            "hidden_control",
            False,
            lambda row: row.get("counterfactual_axis", {}).get("counterfactual_type"),
            "Counterfactual type is target construction metadata and directly exposes generated negatives.",
        ),
        categorical_probe(
            rows,
            labels,
            "metadata_geometry_source",
            "G_e_metadata",
            False,
            lambda row: row.get("G_e", {}).get("geometry_source"),
            "Geometry source names encode anchor, shuffled, wrong-pair, flip, or swap construction.",
        ),
        categorical_probe(
            rows,
            labels,
            "q_generated_counterfactual",
            "Q_e",
            False,
            lambda row: nested_get(row, "Q_e.coverage_features.generated_counterfactual"),
            "This flag is generated from label construction and is a perfect negative shortcut.",
        ),
        categorical_probe(
            rows,
            labels,
            "q_evidence_conflict_flag",
            "Q_e",
            False,
            lambda row: nested_get(row, "Q_e.evidence_conflict_flag"),
            "For this generated dataset, evidence_conflict_flag marks generated negatives, not deployable observability.",
        ),
        categorical_probe(
            rows,
            labels,
            "geometry_status_baseline",
            "metadata",
            False,
            lambda row: row.get("geometry_status_baseline"),
            "Generated rows use a construction status; this must stay out of model inputs.",
        ),
        categorical_probe(
            rows,
            labels,
            "relation_source",
            "metadata",
            False,
            lambda row: row.get("relation_source"),
            "Relation source distinguishes raw anchor rows from generated rows.",
        ),
        categorical_probe(
            rows,
            labels,
            "predicate_label",
            "T_e",
            True,
            lambda row: row.get("T_e", {}).get("predicate_label"),
            "Predicate is intended semantic content; balance should prevent it from solving the target alone.",
        ),
        categorical_probe(
            rows,
            labels,
            "relation_family",
            "T_e",
            True,
            lambda row: row.get("T_e", {}).get("relation_family"),
            "Family is intended semantic content; family-level balance should prevent it from solving the target alone.",
        ),
        categorical_probe(
            rows,
            labels,
            "source_rank_band",
            "Z_e",
            True,
            lambda row: row.get("Z_e", {}).get("source_rank_band"),
            "Z_e can be used in final reliability, but source rank should not solve compatibility alone.",
        ),
        categorical_probe(
            rows,
            labels,
            "source_score_bin",
            "Z_e",
            True,
            baseline_source_score_bin,
            "Source score can be used in final reliability, but should not solve compatibility alone.",
        ),
    ]

    g_feature_names = sorted({key for row in rows for key in row.get("G_e", {}).get("geometry_features", {})})
    for name in g_feature_names:
        probes.append(
            best_threshold_probe(
                rows,
                labels,
                f"g_threshold_{name}",
                name,
                lambda row, feature=name: row.get("G_e", {}).get("geometry_features", {}).get(feature),
            )
        )
    return probes, [compact_probe_row(probe) for probe in probes]


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, Any] = {
        "rows": len(rows),
        "positive": sum(compatibility_label(row) for row in rows),
        "negative": sum(1 - compatibility_label(row) for row in rows),
        "groups": len({row.get("group_id") for row in rows}),
    }
    by_family = Counter()
    by_predicate = Counter()
    by_counterfactual = Counter()
    for row in rows:
        label = "positive" if compatibility_label(row) else "negative"
        family = row.get("T_e", {}).get("relation_family")
        predicate = row.get("T_e", {}).get("predicate_label")
        ctype = row.get("counterfactual_axis", {}).get("counterfactual_type")
        by_family[f"{family}|{label}"] += 1
        by_predicate[f"{family}|{predicate}|{label}"] += 1
        by_counterfactual[f"{family}|{ctype}|{label}"] += 1
    counts["by_family_label"] = dict(sorted(by_family.items()))
    counts["by_predicate_label"] = dict(sorted(by_predicate.items()))
    counts["by_counterfactual_type"] = dict(sorted(by_counterfactual.items()))
    return counts


def validation_errors(input_root: Path, rows: list[dict[str, Any]], input_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = [
        "summary.json",
        "schema.json",
        "compatibility_rows.jsonl",
        "baseline_view.jsonl",
        "audit_view.jsonl",
        "validation_errors.jsonl",
    ]
    for name in required:
        if not (input_root / name).exists():
            errors.append({"error_type": "missing_input_file", "file": name})
    if input_summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "expected": EXPECTED_INPUT_STATUS, "actual": input_summary.get("status")})
    if input_summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "expected": EXPECTED_INPUT_NEXT, "actual": input_summary.get("next_todo")})
    if input_summary.get("learned_smoke_allowed") is not False:
        errors.append({"error_type": "input_should_not_have_learned_smoke_allowed", "actual": input_summary.get("learned_smoke_allowed")})
    if (input_root / "validation_errors.jsonl").exists() and (input_root / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "input_validation_errors_nonempty"})
    if len(rows) != 400:
        errors.append({"error_type": "unexpected_row_count", "expected": 400, "actual": len(rows)})
    label_counts = Counter(compatibility_label(row) for row in rows)
    if label_counts[1] != 200 or label_counts[0] != 200:
        errors.append({"error_type": "unexpected_label_balance", "positive": label_counts[1], "negative": label_counts[0]})
    if any(row.get("split") != "train" for row in rows):
        errors.append({"error_type": "non_train_rows_present"})
    return errors


def write_report(path: Path, summary: dict[str, Any], top_probes: list[dict[str, Any]]) -> None:
    lines = [
        "# Compatibility Dataset V2 Schema Shortcut Audit",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v2_schema_shortcut_audit/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"compatibility positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"schema_errors = {summary['schema_errors']}",
        f"leakage_high_risk_probes = {summary['leakage_high_risk_probes']}",
        f"full_factorized_view_allowed = {str(summary['full_factorized_view_allowed']).lower()}",
        f"sanitized_view_written = {str(summary['sanitized_view_written']).lower()}",
        f"learned_smoke_allowed = {str(summary['learned_smoke_allowed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Finding",
        "",
        "The 400-row candidate set is balanced at family and predicate level, but the unsanitized",
        "`full_factorized`, `obs_head`, `baseline_view`, and raw metadata views expose generated",
        "counterfactual construction fields. These fields can solve the compatibility target without",
        "learning predicate-geometry compatibility.",
        "",
        "Therefore the current rows are not ready for learned smoke as-is. A sanitized model view was",
        "written that keeps `T_e`, `Z_e`, numeric `G_e`, and sanitized `Q_e`, while removing construction",
        "metadata such as `row_role`, `counterfactual_type`, `geometry_source`, and",
        "`generated_counterfactual`.",
        "",
        "## Top Shortcut Probes",
        "",
        "| Probe | Source | Allowed Input | Accuracy | Risk | Interpretation |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for probe in top_probes:
        lines.append(
            "| {probe_name} | {source} | {allowed} | {accuracy:.3f} | {risk} | {interp} |".format(
                probe_name=probe["probe_name"],
                source=probe["source"],
                allowed=str(probe["allowed_model_input"]).lower(),
                accuracy=float(probe["accuracy"]),
                risk=probe["risk_level"],
                interp=str(probe["interpretation"]).replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Do not run learned compatibility smoke on the raw `compatibility_rows.jsonl` or",
            "  `baseline_view.jsonl`.",
            "- Treat `baseline_view.jsonl` and `audit_view.jsonl` as audit/debug artifacts only.",
            "- Use `sanitized_model_view.jsonl` for the next smoke plan.",
            "- Keep `Q_e` as observability/evidence quality, but remove generated-counterfactual",
            "  construction flags from deployable model input.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary = read_json(args.input_root / "summary.json")
    materialization_schema = read_json(args.input_root / "schema.json")
    rows = read_jsonl(args.input_root / "compatibility_rows.jsonl")

    errors = validation_errors(args.input_root, rows, input_summary)
    schema = schema_audit(rows, materialization_schema)
    errors.extend(schema["schema_errors"])

    probes, probe_rows = run_probes(rows)
    leakage_probes = [
        probe
        for probe in probes
        if not probe["allowed_model_input"] and probe["risk_level"] == "high"
    ]
    unsafe_full_view = bool(leakage_probes or schema["unsafe_metadata_hits"])

    sanitized_rows = sanitized_model_rows(rows)
    write_jsonl(args.output_dir / "sanitized_model_view.jsonl", sanitized_rows)

    blocked_fields = {
        "schema_version": SCHEMA_VERSION,
        "blocked_fields": UNSAFE_FULL_VIEW_FIELDS,
        "blocked_views": [
            "raw compatibility_rows model_views.full_factorized",
            "raw compatibility_rows model_views.obs_head",
            "baseline_view.jsonl as model input",
            "audit_view.jsonl as model input",
        ],
        "allowed_next_view": "sanitized_model_view.jsonl",
        "reason": "Generated-counterfactual construction metadata is perfectly predictive of the target.",
    }

    status = STATUS_ERROR if errors else (STATUS_REQUIRES_SANITIZED_VIEW if unsafe_full_view else STATUS_READY)
    next_todo = NEXT_TODO_BLOCKED if status != STATUS_READY else NEXT_TODO_READY

    top_probes = sorted(probe_rows, key=lambda probe: (float(probe["accuracy"]), probe["probe_name"]), reverse=True)[:12]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "input_root": rel_path(args.input_root),
        "output_root": rel_path(args.output_dir),
        "counts": count_summary(rows),
        "validation_errors": len(errors),
        "schema_errors": len(schema["schema_errors"]),
        "schema_warnings": len(schema["schema_warnings"]),
        "leakage_high_risk_probes": len(leakage_probes),
        "full_factorized_view_allowed": False if unsafe_full_view else True,
        "obs_head_view_allowed": False if unsafe_full_view else True,
        "compatibility_main_raw_allowed": False,
        "compatibility_numeric_sanitized_allowed": not errors,
        "sanitized_view_written": True,
        "learned_smoke_allowed": False,
        "sanitized_smoke_plan_allowed": not errors,
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_only_schema_shortcut_audit",
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "raw_full_factorized_view_promoted": False,
        },
        "top_shortcut_probes": top_probes,
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "schema_audit": rel_path(args.output_dir / "schema_audit.json"),
            "shortcut_probe": rel_path(args.output_dir / "shortcut_probe.csv"),
            "shortcut_probe_details": rel_path(args.output_dir / "shortcut_probe_details.json"),
            "sanitized_model_view": rel_path(args.output_dir / "sanitized_model_view.jsonl"),
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "schema_audit.json", schema)
    write_csv(args.output_dir / "shortcut_probe.csv", probe_rows)
    write_json(args.output_dir / "shortcut_probe_details.json", probes)
    write_json(args.output_dir / "blocked_fields.json", blocked_fields)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, top_probes)


if __name__ == "__main__":
    main()
