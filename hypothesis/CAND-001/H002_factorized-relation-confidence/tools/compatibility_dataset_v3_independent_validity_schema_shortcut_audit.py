#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for independent-validity H002 rows."""

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

DEFAULT_INPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_schema_shortcut_audit"

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_independent_validity_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_v1"
SANITIZED_SCHEMA = "h002_independent_validity_primary_binary_sanitized_view_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_blocked_shortcut_risk"
STATUS_ERROR = "h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_input_errors"
NEXT_READY = "compatibility_dataset_v3_independent_validity_sanitized_view_smoke_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit"

EXPECTED_TOTAL_ROWS = 4027
EXPECTED_PRIMARY_ROWS = 3200
EXPECTED_PRIMARY_LABELS = Counter({0: 1600, 1: 1600})

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

MODEL_FEATURE_ROOT = "feature_blocks"
BLOCKED_FEATURE_PATH_FRAGMENTS = (
    "target",
    "hidden",
    "control",
    "construction",
    "counterfactual",
    "anchor",
    "raw_source",
    "row_id",
    "cv_group",
    "scan_id",
    "subject_id",
    "object_id",
    "prediction_id",
    "source_line_no",
    "visible_pair",
    "matched_predicates",
    "matched_gt_ids",
    "label_match",
    "target_pool",
    "target_role",
    "geometry_status",
    "p_geom_valid",
    "consistency_score",
    "geometry_residual_proxy",
    "selection_pass",
)
BLOCKED_G_SUMMARY_FIELDS = {
    "consistency_score",
    "geometry_axis",
    "geometry_residual_proxy",
    "geometry_status",
    "p_geom_valid",
}


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
        return f"{value:.8g}"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def risk_level(accuracy: float) -> str:
    if accuracy >= HIGH_RISK_ACC:
        return "high"
    if accuracy >= MEDIUM_RISK_ACC:
        return "medium"
    return "low"


def flatten_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child_value in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(flatten_paths(child_value, child))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def blocked_fragments_for_feature_path(path: str) -> list[str]:
    lower = path.lower()
    if lower.startswith("feature_blocks.t_e."):
        return []
    if lower.startswith("feature_blocks.z_e_safe."):
        return []
    if lower.startswith("feature_blocks.q_e_safe."):
        if lower.endswith(".has_uncertain_geometry"):
            return ["has_uncertain_geometry"]
        return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
    if lower.startswith("feature_blocks.g_e_raw."):
        return []
    return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]


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
    majority_by_value = {
        key: {
            "majority_label": "positive" if counter[1] >= counter[0] else "negative",
            "negative": counter[0],
            "positive": counter[1],
            "rows": sum(counter.values()),
        }
        for key, counter in sorted(groups.items())
    }
    return {
        "accuracy": round(accuracy, 6),
        "allowed_feature": allowed_feature,
        "best_rule": "per_value_majority",
        "interpretation": interpretation,
        "majority_by_value": majority_by_value,
        "num_values": len(groups),
        "probe_name": probe_name,
        "probe_type": "categorical_majority",
        "risk_level": risk_level(accuracy),
        "source": source,
    }


def numeric_threshold_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    probe_name: str,
    source: str,
    allowed_feature: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
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
            "accuracy": 0.0,
            "allowed_feature": allowed_feature,
            "best_rule": "no_numeric_values",
            "interpretation": interpretation,
            "missing": missing,
            "num_values": 0,
            "probe_name": probe_name,
            "probe_type": "numeric_threshold",
            "risk_level": "low",
            "source": source,
        }

    values = sorted({value for value, _ in pairs})
    if len(values) > 2500:
        step = max(1, len(values) // 2500)
        thresholds = values[::step]
    else:
        thresholds = values
    if len(values) > 1:
        thresholds = [values[0] - 1e-9] + thresholds + [values[-1] + 1e-9]
    best_acc = -1.0
    best_rule = ""
    fallback = 1 if labels.count(1) >= labels.count(0) else 0
    for threshold in thresholds:
        for direction in ("ge", "lt"):
            correct = 0
            for row, label in zip(rows, labels):
                value = safe_float(value_fn(row))
                if value is None:
                    pred = fallback
                else:
                    pred = 1 if (value >= threshold if direction == "ge" else value < threshold) else 0
                correct += int(pred == label)
            acc = correct / len(labels) if labels else 0.0
            if acc > best_acc:
                best_acc = acc
                best_rule = f"{direction}_{threshold:.8g}"

    return {
        "accuracy": round(best_acc, 6),
        "allowed_feature": allowed_feature,
        "best_rule": best_rule,
        "interpretation": interpretation,
        "missing": missing,
        "num_values": len(values),
        "probe_name": probe_name,
        "probe_type": "numeric_threshold",
        "risk_level": risk_level(best_acc),
        "source": source,
    }


def combo_value(row: dict[str, Any], paths: list[str]) -> str:
    return " | ".join(value_key(nested_get(row, path)) for path in paths)


def validate_inputs(summary: dict[str, Any], input_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"scope": "input_summary", "field": "status", "observed": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"scope": "input_summary", "field": "next_todo", "observed": summary.get("next_todo")})
    if int(summary.get("validation_errors", -1)) != 0:
        errors.append({"scope": "input_summary", "field": "validation_errors", "observed": summary.get("validation_errors")})
    for file_name in ["candidate_rows.jsonl", "smoke_ready_view.jsonl", "hidden_manifest.jsonl", "validation_errors.jsonl"]:
        path = input_root / file_name
        if not path.exists():
            errors.append({"scope": "input_files", "field": file_name, "observed": "missing"})
    validation_path = input_root / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"scope": "input_validation_errors", "field": "validation_errors.jsonl", "observed": "non_empty"})
    return errors


def primary_candidate_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in candidate_rows if row.get("labels", {}).get("primary_binary_usable") is True]


def make_sanitized_primary_view(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    view: list[dict[str, Any]] = []
    for row in primary_candidate_rows(candidate_rows):
        features = row["feature_blocks"]
        raw_g = features["G_e"].get("raw_geometry_feature_vector") or {}
        q_e = dict(features["Q_e_safe"])
        q_e.pop("has_uncertain_geometry", None)
        view.append(
            {
                "cv_group_id": row["cv_group_id"],
                "example_id": row["row_id"],
                "family": row["family"],
                "feature_blocks": {
                    "G_e_raw": raw_g,
                    "Q_e_safe": q_e,
                    "T_e": features["T_e"],
                    "Z_e_safe": features["Z_e_safe"],
                },
                "schema_version": SANITIZED_SCHEMA,
                "split": row["split"],
                "target_y": int(row["labels"]["primary_binary"]),
                "target_name": "C_e_independent_validity_primary_binary",
            }
        )
    return view


def audit_feature_paths(sanitized_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    paths = sorted({path for row in sanitized_rows for path in flatten_paths(row.get(MODEL_FEATURE_ROOT, {}), MODEL_FEATURE_ROOT)})
    rows: list[dict[str, Any]] = []
    blocked_count = 0
    for path in paths:
        fragments = blocked_fragments_for_feature_path(path)
        blocked = bool(fragments)
        blocked_count += int(blocked)
        rows.append(
            {
                "blocked": blocked,
                "blocked_fragments": "|".join(fragments),
                "feature_path": path,
                "status": "fail" if blocked else "pass",
            }
        )
    return rows, blocked_count


def audit_blocked_fields(
    candidate_rows: list[dict[str, Any]],
    input_smoke_rows: list[dict[str, Any]],
    sanitized_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int]:
    candidate_paths = sorted({path for row in candidate_rows for path in flatten_paths(row)})
    input_smoke_paths = sorted({path for row in input_smoke_rows for path in flatten_paths(row)})
    sanitized_paths = sorted({path for row in sanitized_rows for path in flatten_paths(row)})
    blocked_fields = [
        "controls_hidden",
        "labels",
        "target_role",
        "target_pool",
        "provenance_safe.selection_pass",
        "feature_blocks.G_e.geometry_status",
        "feature_blocks.G_e.p_geom_valid",
        "feature_blocks.G_e.consistency_score",
        "feature_blocks.G_e.geometry_residual_proxy",
        "feature_blocks.G_e.geometry_axis",
        "feature_blocks.Q_e_safe.has_uncertain_geometry",
    ]
    rows: list[dict[str, Any]] = []
    input_hits = 0
    sanitized_hits = 0
    for field in blocked_fields:
        in_candidate = any(path == field or path.startswith(field + ".") for path in candidate_paths)
        in_input_smoke_feature = any(
            path == field or path.startswith(field + ".") for path in input_smoke_paths if path.startswith("feature_blocks.")
        )
        in_sanitized_feature = any(
            path == field or path.startswith(field + ".") for path in sanitized_paths if path.startswith("feature_blocks.")
        )
        input_hits += int(in_input_smoke_feature)
        sanitized_hits += int(in_sanitized_feature)
        rows.append(
            {
                "blocked_field": field,
                "present_in_candidate_rows": in_candidate,
                "present_in_input_smoke_feature_blocks": in_input_smoke_feature,
                "present_in_sanitized_feature_blocks": in_sanitized_feature,
                "status": "fail" if in_sanitized_feature else "pass",
            }
        )
    return rows, input_hits, sanitized_hits


def validate_counts(
    candidate_rows: list[dict[str, Any]],
    input_smoke_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    sanitized_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    primary_rows = primary_candidate_rows(candidate_rows)
    labels = Counter(int(row["labels"]["primary_binary"]) for row in primary_rows)
    if len(candidate_rows) != EXPECTED_TOTAL_ROWS:
        errors.append({"scope": "counts", "field": "candidate_rows", "observed": len(candidate_rows)})
    if len(input_smoke_rows) != EXPECTED_TOTAL_ROWS:
        errors.append({"scope": "counts", "field": "input_smoke_ready_view", "observed": len(input_smoke_rows)})
    if len(hidden_rows) != EXPECTED_TOTAL_ROWS:
        errors.append({"scope": "counts", "field": "hidden_manifest_rows", "observed": len(hidden_rows)})
    if len(primary_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"scope": "counts", "field": "primary_binary_rows", "observed": len(primary_rows)})
    if len(sanitized_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"scope": "counts", "field": "sanitized_primary_rows", "observed": len(sanitized_rows)})
    if labels != EXPECTED_PRIMARY_LABELS:
        errors.append({"scope": "counts", "field": "primary_binary_label_counts", "observed": dict(labels)})
    return errors


def build_distribution_rows(candidate_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden_by_id = {row["row_id"]: row for row in hidden_rows}
    primary = primary_candidate_rows(candidate_rows)
    axes: list[tuple[str, Callable[[dict[str, Any], dict[str, Any] | None], Any]]] = [
        ("family", lambda row, hidden: row["family"]),
        ("target_pool", lambda row, hidden: row.get("target_pool")),
        ("predicate", lambda row, hidden: nested_get(row, "feature_blocks.T_e.predicate_label")),
        ("subject_object_pair", lambda row, hidden: (
            nested_get(row, "feature_blocks.T_e.subject_class_label"),
            nested_get(row, "feature_blocks.T_e.object_class_label"),
        )),
        ("rank_band", lambda row, hidden: nested_get(row, "feature_blocks.Z_e_safe.rank_band")),
        ("geometry_status", lambda row, hidden: nested_get(row, "feature_blocks.G_e.geometry_status")),
        ("selection_pass", lambda row, hidden: nested_get(row, "provenance_safe.selection_pass")),
        ("visible_pair", lambda row, hidden: nested_get(hidden or {}, "controls_hidden.visible_pair")),
    ]
    rows: list[dict[str, Any]] = []
    for axis, fn in axes:
        counters: dict[str, Counter[int]] = defaultdict(Counter)
        for row in primary:
            hidden = hidden_by_id.get(row["row_id"])
            counters[value_key(fn(row, hidden))][int(row["labels"]["primary_binary"])] += 1
        for value, counter in sorted(counters.items()):
            rows.append(
                {
                    "axis": axis,
                    "value": value,
                    "rows": sum(counter.values()),
                    "positive": counter[1],
                    "negative": counter[0],
                    "positive_rate": round(counter[1] / sum(counter.values()), 6) if sum(counter.values()) else 0.0,
                }
            )
    return rows


def build_probes(
    candidate_rows: list[dict[str, Any]],
    sanitized_rows: list[dict[str, Any]],
    input_smoke_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = [int(row["target_y"]) for row in sanitized_rows]
    probes: list[dict[str, Any]] = []

    def add(probe: dict[str, Any]) -> None:
        probes.append(probe)

    # Allowed sanitized feature probes. Medium/high here blocks learned smoke.
    allowed_categorical: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("family", lambda row: row["family"], "Family is allowed metadata but should be balanced by construction."),
        ("predicate_label", lambda row: nested_get(row, "feature_blocks.T_e.predicate_label"), "Predicate alone should not solve relation validity."),
        ("subject_class_label", lambda row: nested_get(row, "feature_blocks.T_e.subject_class_label"), "Subject class alone should not solve the target."),
        ("object_class_label", lambda row: nested_get(row, "feature_blocks.T_e.object_class_label"), "Object class alone should not solve the target."),
        (
            "subject_object_class_pair",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
            "Class-pair shortcut risk captures the visible-pair concentration caused by materialization.",
        ),
        (
            "predicate_x_class_pair",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.predicate_label"),
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
            "Predicate plus object-pair semantics should not memorize the target.",
        ),
        ("rank_band", lambda row: nested_get(row, "feature_blocks.Z_e_safe.rank_band"), "Rank band should not solve validity."),
        ("coverage_state", lambda row: nested_get(row, "feature_blocks.Q_e_safe.coverage_state"), "Coverage state should not solve primary binary validity."),
        ("reason_code_count", lambda row: nested_get(row, "feature_blocks.Q_e_safe.reason_code_count"), "Reason-code count is a coarse quality signal only."),
    ]
    for name, fn, interpretation in allowed_categorical:
        add(categorical_probe(sanitized_rows, labels, name, "allowed_sanitized_feature", True, fn, interpretation))

    allowed_numeric: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("semantic_score_norm", lambda row: nested_get(row, "feature_blocks.Z_e_safe.semantic_score_norm"), "Source confidence alone should not solve validity."),
        ("semantic_score_raw", lambda row: nested_get(row, "feature_blocks.Z_e_safe.semantic_score_raw"), "Raw source confidence alone should not solve validity."),
        ("semantic_rank", lambda row: nested_get(row, "feature_blocks.Z_e_safe.semantic_rank"), "Source rank alone should not solve validity."),
        ("predicate_rank_for_pair", lambda row: nested_get(row, "feature_blocks.Z_e_safe.predicate_rank_for_pair"), "Pair-level predicate rank should not solve validity."),
        ("context_prediction_count", lambda row: nested_get(row, "feature_blocks.Z_e_safe.context_prediction_count"), "Context count is source metadata and should not solve validity."),
        ("raw_geometry_feature_count", lambda row: nested_get(row, "feature_blocks.Q_e_safe.raw_geometry_feature_count"), "Raw geometry feature count should not solve validity."),
    ]
    raw_fields = sorted(
        {
            key
            for row in sanitized_rows
            for key in (nested_get(row, "feature_blocks.G_e_raw", {}) or {}).keys()
        }
    )
    for field in raw_fields:
        allowed_numeric.append(
            (
                f"G_e_raw.{field}",
                lambda row, field=field: nested_get(row, f"feature_blocks.G_e_raw.{field}"),
                "Single raw geometry evidence field should not by itself solve the primary target.",
            )
        )
    for name, fn, interpretation in allowed_numeric:
        add(numeric_threshold_probe(sanitized_rows, labels, name, "allowed_sanitized_feature", True, fn, interpretation))

    # Blocked construction-summary probes from the materializer's first smoke view.
    primary_input_smoke = [row for row in input_smoke_rows if row.get("target", {}).get("primary_binary_usable") is True]
    input_labels = [int(row["target"]["primary_binary"]) for row in primary_input_smoke]
    for field in sorted(BLOCKED_G_SUMMARY_FIELDS):
        fn = (
            (lambda row, field=field: nested_get(row, f"feature_blocks.G_e.{field}"))
            if field != "geometry_axis"
            else (lambda row: nested_get(row, "feature_blocks.G_e.geometry_axis"))
        )
        probe_fn = categorical_probe if field in {"geometry_axis", "geometry_status"} else numeric_threshold_probe
        add(
            probe_fn(
                primary_input_smoke,
                input_labels,
                f"blocked_G_e_summary.{field}",
                "blocked_construction_summary",
                False,
                fn,
                "Construction-derived geometry summary is blocked from the sanitized model view.",
            )
        )

    # Hidden/provenance probes. High risk is expected only because these fields are blocked.
    hidden_by_id = {row["row_id"]: row for row in hidden_rows}
    primary_candidate = primary_candidate_rows(candidate_rows)
    raw_labels = [int(row["labels"]["primary_binary"]) for row in primary_candidate]

    def hidden_for(row: dict[str, Any], dotted: str) -> Any:
        return nested_get(hidden_by_id.get(row["row_id"], {}), dotted)

    blocked_categorical: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("raw_row_id", lambda row: row.get("row_id"), "Row id is blocked metadata."),
        ("raw_cv_group_id", lambda row: row.get("cv_group_id"), "CV group id is blocked from features."),
        ("target_pool", lambda row: row.get("target_pool"), "Target pool is construction metadata."),
        ("target_role", lambda row: row.get("target_role"), "Target role is construction metadata."),
        ("selection_pass", lambda row: nested_get(row, "provenance_safe.selection_pass"), "Selection pass is materialization metadata."),
        ("hidden_label_match_status", lambda row: hidden_for(row, "controls_hidden.label_match_status"), "GT join label is target-construction metadata."),
        ("hidden_visible_pair", lambda row: hidden_for(row, "controls_hidden.visible_pair"), "Visible pair is audit-only metadata."),
        ("hidden_scan_id", lambda row: hidden_for(row, "controls_hidden.scan_id"), "Scan id is provenance."),
        ("hidden_prediction_id", lambda row: hidden_for(row, "controls_hidden.prediction_id"), "Prediction id is a row identifier."),
        (
            "hidden_visible_pair_x_predicate",
            lambda row: (
                hidden_for(row, "controls_hidden.visible_pair"),
                nested_get(row, "feature_blocks.T_e.predicate_label"),
            ),
            "Visible pair plus predicate tests the known materialization concentration risk.",
        ),
        ("target_label_self", lambda row: nested_get(row, "labels.primary_binary"), "The target itself is blocked."),
    ]
    for name, fn, interpretation in blocked_categorical:
        add(categorical_probe(primary_candidate, raw_labels, name, "blocked_raw_or_hidden", False, fn, interpretation))

    summary_rows = [
        {
            "accuracy": probe["accuracy"],
            "allowed_feature": probe["allowed_feature"],
            "best_rule": probe.get("best_rule", ""),
            "missing": probe.get("missing", ""),
            "num_values": probe.get("num_values", ""),
            "probe_name": probe["probe_name"],
            "probe_type": probe["probe_type"],
            "risk_level": probe["risk_level"],
            "source": probe["source"],
        }
        for probe in probes
    ]
    return summary_rows, probes


def build_contract(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_feature_roots": [
            "feature_blocks.T_e",
            "feature_blocks.Z_e_safe",
            "feature_blocks.G_e_raw",
            "feature_blocks.Q_e_safe",
        ],
        "blocked_from_sanitized_view": sorted(BLOCKED_G_SUMMARY_FIELDS | {"has_uncertain_geometry"}),
        "cv_group_id": "grouped-CV metadata only",
        "next_todo": summary["next_todo"],
        "schema_version": SANITIZED_SCHEMA,
        "target_field": "target_y",
        "train_only": True,
        "usage_boundary": summary["boundary"],
    }


def build_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    risk = summary["risk_summary"]
    outputs = summary["output_paths"]
    blocked_names = ", ".join(risk["allowed_feature_high_or_medium_probe_names"]) or "none"
    return "\n".join(
        [
            "# H002 Independent Validity Schema Shortcut Audit",
            "",
            "## Status",
            "",
            f"- status: `{summary['status']}`",
            f"- validation_errors: `{summary['validation_errors']}`",
            f"- next_todo: `{summary['next_todo']}`",
            "",
            "## Counts",
            "",
            f"- candidate_rows: `{counts['candidate_rows']}`",
            f"- primary_binary_rows: `{counts['primary_binary_rows']}`",
            f"- sanitized_primary_rows: `{counts['sanitized_primary_rows']}`",
            f"- primary_label_counts: `{counts['primary_label_counts']}`",
            f"- family_counts: `{counts['primary_family_counts']}`",
            "",
            "## Shortcut Result",
            "",
            f"- allowed_high_or_medium_risk: `{risk['allowed_feature_high_or_medium_risk']}`",
            f"- allowed_high_risk: `{risk['allowed_feature_high_risk']}`",
            f"- allowed_medium_risk: `{risk['allowed_feature_medium_risk']}`",
            f"- blocked_construction_high_risk: `{risk['blocked_construction_high_risk']}`",
            f"- blocked_raw_hidden_high_risk: `{risk['blocked_raw_hidden_high_risk']}`",
            f"- sanitized_blocked_feature_path_hits: `{risk['sanitized_blocked_feature_path_hits']}`",
            f"- sanitized_blocked_field_leakage_hits: `{risk['sanitized_blocked_field_leakage_hits']}`",
            f"- blocked allowed probes: `{blocked_names}`",
            "",
            "Interpretation:",
            "",
            "- The materializer's first smoke view contained construction-derived geometry summaries; the audit writes a stricter raw-only sanitized view.",
            "- The sanitized view still has allowed-feature shortcut risk, mainly from semantic object-pair concentration.",
            "- Therefore this stage blocks learned smoke and routes to a path decision rather than claiming independent validity success.",
            "",
            "## Outputs",
            "",
            f"- sanitized primary view: `{outputs['sanitized_primary_view']}`",
            f"- shortcut probes: `{outputs['shortcut_probes']}`",
            f"- shortcut details: `{outputs['shortcut_probe_details']}`",
            f"- distribution audit: `{outputs['distribution_audit']}`",
            f"- blocked field audit: `{outputs['blocked_field_audit']}`",
            f"- feature path audit: `{outputs['feature_path_audit']}`",
            f"- summary: `{outputs['summary']}`",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    input_summary = read_json(args.input_root / "summary.json")
    candidate_rows = read_jsonl(args.input_root / "candidate_rows.jsonl")
    input_smoke_rows = read_jsonl(args.input_root / "smoke_ready_view.jsonl")
    hidden_rows = read_jsonl(args.input_root / "hidden_manifest.jsonl")

    errors.extend(validate_inputs(input_summary, args.input_root))

    sanitized_rows = make_sanitized_primary_view(candidate_rows)
    errors.extend(validate_counts(candidate_rows, input_smoke_rows, hidden_rows, sanitized_rows))

    feature_path_rows, sanitized_blocked_feature_path_hits = audit_feature_paths(sanitized_rows)
    blocked_field_rows, input_blocked_field_hits, sanitized_blocked_field_hits = audit_blocked_fields(
        candidate_rows, input_smoke_rows, sanitized_rows
    )
    probe_rows, probe_details = build_probes(candidate_rows, sanitized_rows, input_smoke_rows, hidden_rows)
    distribution_rows = build_distribution_rows(candidate_rows, hidden_rows)

    allowed_high_or_medium = [
        row for row in probe_rows if row["allowed_feature"] and row["risk_level"] in {"high", "medium"}
    ]
    allowed_high = [row for row in allowed_high_or_medium if row["risk_level"] == "high"]
    allowed_medium = [row for row in allowed_high_or_medium if row["risk_level"] == "medium"]
    blocked_construction_high = [
        row for row in probe_rows if row["source"] == "blocked_construction_summary" and row["risk_level"] == "high"
    ]
    blocked_raw_hidden_high = [
        row for row in probe_rows if row["source"] == "blocked_raw_or_hidden" and row["risk_level"] == "high"
    ]

    if sanitized_blocked_feature_path_hits:
        errors.append(
            {
                "scope": "feature_path_audit",
                "field": "sanitized_blocked_feature_path_hits",
                "observed": sanitized_blocked_feature_path_hits,
            }
        )
    if sanitized_blocked_field_hits:
        errors.append(
            {
                "scope": "blocked_field_audit",
                "field": "sanitized_blocked_field_leakage_hits",
                "observed": sanitized_blocked_field_hits,
            }
        )
    if allowed_high_or_medium:
        errors.append(
            {
                "scope": "shortcut_probes",
                "field": "allowed_feature_high_or_medium_risk",
                "observed": [row["probe_name"] for row in allowed_high_or_medium],
            }
        )

    status = STATUS_ERROR if any(err.get("scope") in {"input_summary", "input_files", "counts"} for err in errors) else (
        STATUS_BLOCKED if errors else STATUS_READY
    )
    next_todo = NEXT_BLOCKED if status == STATUS_BLOCKED else (NEXT_READY if status == STATUS_READY else "fix_independent_validity_schema_shortcut_audit_inputs")
    output_paths = {
        "blocked_field_audit": args.output_dir / "blocked_field_audit.csv",
        "distribution_audit": args.output_dir / "distribution_audit.csv",
        "feature_path_audit": args.output_dir / "feature_path_audit.csv",
        "report": args.output_dir / "report.md",
        "sanitized_primary_view": args.output_dir / "sanitized_primary_view.jsonl",
        "smoke_ready_model_view_contract": args.output_dir / "smoke_ready_model_view_contract.json",
        "shortcut_probe_details": args.output_dir / "shortcut_probe_details.jsonl",
        "shortcut_probes": args.output_dir / "shortcut_probes.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    boundary = {
        "h001_artifacts_modified": False,
        "materializes_candidate_rows": False,
        "paper_evidence_allowed": False,
        "runs_learned_smoke": False,
        "schema_shortcut_audit_only": True,
        "split": "train_only_schema_shortcut_audit",
        "test_usage": False,
        "trains_new_model": False,
        "validation_usage": False,
    }
    primary_rows = primary_candidate_rows(candidate_rows)
    counts = {
        "candidate_rows": len(candidate_rows),
        "hidden_manifest_rows": len(hidden_rows),
        "input_smoke_rows": len(input_smoke_rows),
        "nonbinary_rows": len(candidate_rows) - len(primary_rows),
        "primary_binary_rows": len(primary_rows),
        "primary_family_counts": dict(Counter(row["family"] for row in primary_rows)),
        "primary_label_counts": {str(k): v for k, v in sorted(Counter(int(row["labels"]["primary_binary"]) for row in primary_rows).items())},
        "sanitized_primary_rows": len(sanitized_rows),
    }
    risk_summary = {
        "allowed_feature_high_or_medium_risk": len(allowed_high_or_medium),
        "allowed_feature_high_or_medium_probe_names": [row["probe_name"] for row in allowed_high_or_medium],
        "allowed_feature_high_risk": len(allowed_high),
        "allowed_feature_medium_risk": len(allowed_medium),
        "blocked_construction_high_risk": len(blocked_construction_high),
        "blocked_construction_high_risk_probe_names": [row["probe_name"] for row in blocked_construction_high],
        "blocked_raw_hidden_high_risk": len(blocked_raw_hidden_high),
        "input_blocked_field_hits": input_blocked_field_hits,
        "sanitized_blocked_feature_path_hits": sanitized_blocked_feature_path_hits,
        "sanitized_blocked_field_leakage_hits": sanitized_blocked_field_hits,
    }
    summary = {
        "boundary": boundary,
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "candidate_rows": rel_path(args.input_root / "candidate_rows.jsonl"),
            "hidden_manifest": rel_path(args.input_root / "hidden_manifest.jsonl"),
            "input_smoke_ready_view": rel_path(args.input_root / "smoke_ready_view.jsonl"),
            "input_summary": rel_path(args.input_root / "summary.json"),
        },
        "input_status": input_summary.get("status"),
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "path_decision": {
            "learned_smoke_allowed": status == STATUS_READY,
            "next_todo": next_todo,
            "paper_evidence_allowed": False,
            "rationale": (
                "Allowed sanitized features still show shortcut risk; run a path decision before learned smoke."
                if status == STATUS_BLOCKED
                else "Schema and shortcut audit passed; plan sanitized-view smoke next."
            ),
            "sanitized_view_smoke_plan_allowed": status == STATUS_READY,
            "selected_path": (
                "independent_validity_path_decision_after_schema_shortcut_audit"
                if status == STATUS_BLOCKED
                else "write_independent_validity_sanitized_view_smoke_plan"
            ),
            "status": status,
            "validation_errors": len(errors),
        },
        "risk_summary": risk_summary,
        "schema_version": SCHEMA_VERSION,
        "selected_path": "audit_independent_validity_schema_and_shortcuts",
        "smoke_ready_schema": SANITIZED_SCHEMA,
        "status": status,
        "validation_errors": len(errors),
    }

    write_jsonl(output_paths["sanitized_primary_view"], sanitized_rows)
    write_json(output_paths["smoke_ready_model_view_contract"], build_contract(summary))
    write_csv(output_paths["shortcut_probes"], probe_rows)
    write_jsonl(output_paths["shortcut_probe_details"], probe_details)
    write_csv(output_paths["distribution_audit"], distribution_rows)
    write_csv(output_paths["blocked_field_audit"], blocked_field_rows)
    write_csv(output_paths["feature_path_audit"], feature_path_rows)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps({"status": status, "validation_errors": len(errors), "risk_summary": risk_summary}, sort_keys=True))
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
