#!/usr/bin/env python3
"""Audit schema leakage and residual shortcuts for exact-stratum repaired H002 rows."""

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

DEFAULT_INPUT_ROOT = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_v1"
SANITIZED_SCHEMA = "h002_exact_stratum_repaired_independent_validity_sanitized_primary_view_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_blocked_residual_shortcut_risk"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_input_errors"
NEXT_READY = "compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_independent_validity_stratum_repair_path_decision_after_schema_shortcut_audit"

EXPECTED_PRIMARY_ROWS = 1600
EXPECTED_LABELS = Counter({0: 800, 1: 800})
EXPECTED_MIN_STRATA = 30

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

MODEL_FEATURE_ROOT = "feature_blocks"
CRITICAL_SHORTCUT_PROBES = {
    "family",
    "object_class_label",
    "predicate_label",
    "predicate_x_class_pair",
    "rank_band",
    "source_id",
    "subject_class_label",
    "subject_object_class_pair",
}
SOURCE_CONFIDENCE_PROBES = {
    "semantic_rank",
    "semantic_score_norm",
    "semantic_score_raw",
}
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
    "geometry_axis",
    "selection_pass",
    "scope_role",
    "stratum_id",
)
FORBIDDEN_MODEL_KEYS = set(BLOCKED_FEATURE_PATH_FRAGMENTS)


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
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(flatten_paths(child, child_prefix))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def nested_key_hits(payload: Any, forbidden: set[str]) -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in forbidden:
                hits.append(key)
            hits.extend(nested_key_hits(value, forbidden))
    elif isinstance(payload, list):
        for value in payload:
            hits.extend(nested_key_hits(value, forbidden))
    return hits


def blocked_fragments_for_feature_path(path: str) -> list[str]:
    lower = path.lower()
    if lower.startswith("feature_blocks.t_e."):
        return []
    if lower.startswith("feature_blocks.z_e_safe."):
        return []
    if lower.startswith("feature_blocks.q_e_safe."):
        return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
    if lower.startswith("feature_blocks.g_e_raw."):
        return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
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

    fallback = 1 if labels.count(1) >= labels.count(0) else 0
    best_acc = -1.0
    best_rule = ""
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


def validate_inputs(summary: dict[str, Any], input_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"scope": "input_summary", "field": "status", "observed": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"scope": "input_summary", "field": "next_todo", "observed": summary.get("next_todo")})
    if int(summary.get("validation_errors", -1)) != 0:
        errors.append({"scope": "input_summary", "field": "validation_errors", "observed": summary.get("validation_errors")})
    for file_name in [
        "candidate_rows.jsonl",
        "hidden_manifest.jsonl",
        "model_safe_view.jsonl",
        "quota_audit.csv",
        "schema_precheck.json",
        "validation_errors.jsonl",
    ]:
        path = input_root / file_name
        if not path.exists():
            errors.append({"scope": "input_files", "field": file_name, "observed": "missing"})
    validation_path = input_root / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"scope": "input_validation_errors", "field": "validation_errors.jsonl", "observed": "non_empty"})
    return errors


def validate_counts(
    candidate_rows: list[dict[str, Any]],
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    labels = Counter(int(row["target"]["primary_binary"]) for row in model_rows)
    strata = Counter(row["stratum_id"] for row in candidate_rows)
    by_stratum_label: dict[str, Counter[int]] = defaultdict(Counter)
    for row in candidate_rows:
        by_stratum_label[row["stratum_id"]][int(row["labels"]["primary_binary"])] += 1
    failed_strata = [stratum for stratum, counter in by_stratum_label.items() if counter[0] != counter[1]]
    if len(candidate_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"scope": "counts", "field": "candidate_rows", "observed": len(candidate_rows)})
    if len(model_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"scope": "counts", "field": "model_safe_view_rows", "observed": len(model_rows)})
    if len(hidden_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"scope": "counts", "field": "hidden_manifest_rows", "observed": len(hidden_rows)})
    if labels != EXPECTED_LABELS:
        errors.append({"scope": "counts", "field": "primary_binary_label_counts", "observed": dict(labels)})
    if len(strata) < EXPECTED_MIN_STRATA:
        errors.append({"scope": "counts", "field": "retained_exact_strata", "observed": len(strata)})
    if failed_strata:
        errors.append({"scope": "counts", "field": "stratum_internal_balance_failures", "observed": failed_strata[:20]})
    return errors


def make_sanitized_primary_view(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    view: list[dict[str, Any]] = []
    for row in model_rows:
        view.append(
            {
                "cv_group_id": row["cv_group_id"],
                "example_id": row["row_id"],
                "family": row["family"],
                "feature_blocks": row["feature_blocks"],
                "schema_version": SANITIZED_SCHEMA,
                "split": row["split"],
                "target_name": "C_e_independent_validity_exact_stratum_repaired_primary_binary",
                "target_y": int(row["target"]["primary_binary"]),
                "text": row.get("text", {}),
            }
        )
    return view


def audit_feature_paths(sanitized_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    paths = sorted(
        {
            path
            for row in sanitized_rows
            for path in flatten_paths(row.get(MODEL_FEATURE_ROOT, {}), MODEL_FEATURE_ROOT)
        }
    )
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


def audit_blocked_fields(model_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    full_hits = Counter()
    feature_hits = Counter()
    for row in model_rows:
        full_hits.update(nested_key_hits(row, FORBIDDEN_MODEL_KEYS))
        feature_hits.update(nested_key_hits(row.get("feature_blocks", {}), FORBIDDEN_MODEL_KEYS))
    rows: list[dict[str, Any]] = []
    for key in sorted(FORBIDDEN_MODEL_KEYS):
        rows.append(
            {
                "blocked_key": key,
                "feature_hits": feature_hits.get(key, 0),
                "full_model_view_hits": full_hits.get(key, 0),
                "status": "fail" if feature_hits.get(key, 0) else "pass",
            }
        )
    return rows, sum(full_hits.values()), sum(feature_hits.values())


def build_distribution_rows(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden_by_id = {row["row_id"]: row for row in hidden_rows}
    axes: list[tuple[str, Callable[[dict[str, Any], dict[str, Any] | None], Any]]] = [
        ("family", lambda row, hidden: row["family"]),
        ("predicate", lambda row, hidden: nested_get(row, "feature_blocks.T_e.predicate_label")),
        ("subject_object_pair", lambda row, hidden: (
            nested_get(row, "feature_blocks.T_e.subject_class_label"),
            nested_get(row, "feature_blocks.T_e.object_class_label"),
        )),
        ("predicate_x_class_pair", lambda row, hidden: (
            nested_get(row, "feature_blocks.T_e.predicate_label"),
            nested_get(row, "feature_blocks.T_e.subject_class_label"),
            nested_get(row, "feature_blocks.T_e.object_class_label"),
        )),
        ("rank_band", lambda row, hidden: nested_get(row, "feature_blocks.Z_e_safe.rank_band")),
        ("hidden_geometry_status", lambda row, hidden: nested_get(hidden or {}, "controls_hidden.geometry_status")),
        ("hidden_label_match_status", lambda row, hidden: nested_get(hidden or {}, "controls_hidden.label_match_status")),
        ("hidden_stratum_id", lambda row, hidden: nested_get(hidden or {}, "stratum_id")),
    ]
    rows: list[dict[str, Any]] = []
    for axis, fn in axes:
        counters: dict[str, Counter[int]] = defaultdict(Counter)
        for row in model_rows:
            hidden = hidden_by_id.get(row["row_id"])
            counters[value_key(fn(row, hidden))][int(row["target"]["primary_binary"])] += 1
        for value, counter in sorted(counters.items()):
            total = sum(counter.values())
            rows.append(
                {
                    "axis": axis,
                    "negative": counter[0],
                    "positive": counter[1],
                    "positive_rate": round(counter[1] / total, 6) if total else 0.0,
                    "rows": total,
                    "value": value,
                }
            )
    return rows


def raw_geometry_feature_names(model_rows: list[dict[str, Any]]) -> list[str]:
    names = set()
    for row in model_rows:
        raw = nested_get(row, "feature_blocks.G_e_raw.raw_geometry_feature_vector", {}) or {}
        if isinstance(raw, dict):
            names.update(str(key) for key in raw)
    return sorted(names)


def build_probes(
    model_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = [int(row["target"]["primary_binary"]) for row in model_rows]
    probes: list[dict[str, Any]] = []

    def add(probe: dict[str, Any]) -> None:
        probes.append(probe)

    categorical_allowed: list[tuple[str, str, Callable[[dict[str, Any]], Any], str]] = [
        ("family", "critical_semantic_or_source", lambda row: row["family"], "Family should be label-balanced after exact repair."),
        ("predicate_label", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.T_e.predicate_label"), "Predicate should not solve validity."),
        ("subject_class_label", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.T_e.subject_class_label"), "Subject class should not solve validity."),
        ("object_class_label", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.T_e.object_class_label"), "Object class should not solve validity."),
        (
            "subject_object_class_pair",
            "critical_semantic_or_source",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
            "Class pair was a previous shortcut and should be controlled.",
        ),
        (
            "predicate_x_class_pair",
            "critical_semantic_or_source",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.predicate_label"),
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
            "Exact predicate-class repair should drive this probe toward chance.",
        ),
        ("rank_band", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.Z_e_safe.rank_band"), "Rank band should not solve target."),
        ("source_id", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.Z_e_safe.source_id"), "Source id should not solve target."),
    ]
    for name, source, fn, interpretation in categorical_allowed:
        add(categorical_probe(model_rows, labels, name, source, True, fn, interpretation))

    numeric_allowed: list[tuple[str, str, Callable[[dict[str, Any]], Any], str]] = [
        ("semantic_score_norm", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.Z_e_safe.semantic_score_norm"), "Source confidence should not solve target."),
        ("semantic_score_raw", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.Z_e_safe.semantic_score_raw"), "Raw source confidence should not solve target."),
        ("semantic_rank", "critical_semantic_or_source", lambda row: nested_get(row, "feature_blocks.Z_e_safe.semantic_rank"), "Source rank should not solve target."),
        ("raw_geometry_feature_count", "allowed_quality_or_geometry", lambda row: nested_get(row, "feature_blocks.Q_e_safe.raw_geometry_feature_count"), "Feature count is quality metadata."),
        ("object_pair_feature_coverage", "allowed_quality_or_geometry", lambda row: nested_get(row, "feature_blocks.Q_e_safe.object_pair_feature_coverage"), "Coverage should not trivially solve target."),
    ]
    for field in raw_geometry_feature_names(model_rows):
        numeric_allowed.append(
            (
                f"G_e_raw.{field}",
                "allowed_raw_geometry",
                lambda row, field=field: nested_get(row, f"feature_blocks.G_e_raw.raw_geometry_feature_vector.{field}"),
                "Raw geometry evidence may be predictive, but high single-feature accuracy limits factorized-method novelty.",
            )
        )
    for name, source, fn, interpretation in numeric_allowed:
        add(numeric_threshold_probe(model_rows, labels, name, source, True, fn, interpretation))

    hidden_by_id = {row["row_id"]: row for row in hidden_rows}
    candidate_by_id = {row["row_id"]: row for row in candidate_rows}

    def hidden_for(model_row: dict[str, Any], dotted: str) -> Any:
        return nested_get(hidden_by_id.get(model_row["row_id"], {}), dotted)

    def candidate_for(model_row: dict[str, Any], dotted: str) -> Any:
        return nested_get(candidate_by_id.get(model_row["row_id"], {}), dotted)

    blocked_categorical: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("hidden_geometry_status", lambda row: hidden_for(row, "controls_hidden.geometry_status"), "Construction geometry status is hidden-only."),
        ("hidden_label_match_status", lambda row: hidden_for(row, "controls_hidden.label_match_status"), "GT join label status is hidden-only."),
        ("hidden_stratum_id", lambda row: hidden_for(row, "stratum_id"), "Stratum id is selection metadata."),
        ("hidden_target_pool", lambda row: candidate_for(row, "target_pool"), "Target pool is construction metadata."),
        ("hidden_target_role", lambda row: candidate_for(row, "target_role"), "Target role is construction metadata."),
        ("hidden_visible_pair", lambda row: hidden_for(row, "controls_hidden.visible_pair"), "Visible pair is audit-only metadata."),
        ("target_label_self", lambda row: candidate_for(row, "labels.primary_binary"), "Target itself is blocked."),
    ]
    for name, fn, interpretation in blocked_categorical:
        add(categorical_probe(model_rows, labels, name, "blocked_raw_or_hidden", False, fn, interpretation))

    blocked_numeric: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("hidden_p_geom_valid", lambda row: hidden_for(row, "controls_hidden.p_geom_valid"), "Rule-based geometry score is hidden-only baseline/teacher."),
        ("hidden_geometry_residual_proxy", lambda row: hidden_for(row, "controls_hidden.geometry_residual_proxy"), "Residual summary is hidden-only."),
    ]
    for name, fn, interpretation in blocked_numeric:
        add(numeric_threshold_probe(model_rows, labels, name, "blocked_raw_or_hidden", False, fn, interpretation))

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


def build_validation_errors(
    input_errors: list[dict[str, Any]],
    count_errors: list[dict[str, Any]],
    sanitized_blocked_feature_path_hits: int,
    model_feature_blocked_key_hits: int,
    critical_high_or_medium: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = list(input_errors) + list(count_errors)
    if sanitized_blocked_feature_path_hits:
        errors.append(
            {
                "scope": "feature_path_audit",
                "field": "sanitized_blocked_feature_path_hits",
                "observed": sanitized_blocked_feature_path_hits,
            }
        )
    if model_feature_blocked_key_hits:
        errors.append(
            {
                "scope": "blocked_field_audit",
                "field": "model_feature_blocked_key_hits",
                "observed": model_feature_blocked_key_hits,
            }
        )
    if critical_high_or_medium:
        errors.append(
            {
                "scope": "shortcut_probes",
                "field": "critical_semantic_or_source_high_or_medium_risk",
                "observed": [row["probe_name"] for row in critical_high_or_medium],
            }
        )
    return errors


def build_contract(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_feature_roots": [
            "feature_blocks.T_e",
            "feature_blocks.Z_e_safe",
            "feature_blocks.G_e_raw",
            "feature_blocks.Q_e_safe",
        ],
        "blocked_from_model_view": sorted(FORBIDDEN_MODEL_KEYS),
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
    critical = ", ".join(risk["critical_high_or_medium_probe_names"]) or "none"
    source = ", ".join(risk["source_confidence_high_or_medium_probe_names"]) or "none"
    geometry = ", ".join(risk["raw_geometry_high_or_medium_probe_names"]) or "none"
    return "\n".join(
        [
            "# H002 Independent Validity Stratum Repair Schema Shortcut Audit",
            "",
            "## Status",
            "",
            "```text",
            f"status = {summary['status']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Counts",
            "",
            "```text",
            f"model_safe_rows = {counts['model_safe_rows']}",
            f"candidate_rows = {counts['candidate_rows']}",
            f"hidden_manifest_rows = {counts['hidden_manifest_rows']}",
            f"label_counts = {counts['label_counts']}",
            f"family_counts = {counts['family_counts']}",
            f"predicate_counts = {counts['predicate_counts']}",
            "```",
            "",
            "## Shortcut Result",
            "",
            "```text",
            f"critical_high_or_medium = {risk['critical_high_or_medium_risk']}",
            f"source_confidence_high_or_medium = {risk['source_confidence_high_or_medium_risk']}",
            f"raw_geometry_high_or_medium = {risk['raw_geometry_high_or_medium_risk']}",
            f"blocked_hidden_high_risk = {risk['blocked_hidden_high_risk']}",
            f"sanitized_blocked_feature_path_hits = {risk['sanitized_blocked_feature_path_hits']}",
            f"model_feature_blocked_key_hits = {risk['model_feature_blocked_key_hits']}",
            "```",
            "",
            f"Critical blocked probes: `{critical}`",
            "",
            f"Source confidence warnings: `{source}`",
            "",
            f"Raw geometry warnings: `{geometry}`",
            "",
            "Interpretation:",
            "",
            "- Exact predicate/object-class balancing is considered successful only if the critical semantic/source probes are low-risk.",
            "- Raw geometry probes are reported separately because `G_e_raw` is a legitimate evidence input; high single-feature performance is a novelty/baseline caveat, not schema leakage.",
            "- Hidden construction fields may be highly predictive, but they must remain outside the model-safe view.",
            "",
            "## Boundary",
            "",
            "- Train-only schema/shortcut audit.",
            "- No validation/test usage.",
            "- No learned smoke or model training.",
            "- No H001 artifact modification.",
            "- Not paper evidence.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary = read_json(args.input_root / "summary.json")
    candidate_rows = read_jsonl(args.input_root / "candidate_rows.jsonl")
    model_rows = read_jsonl(args.input_root / "model_safe_view.jsonl")
    hidden_rows = read_jsonl(args.input_root / "hidden_manifest.jsonl")

    input_errors = validate_inputs(input_summary, args.input_root)
    count_errors = validate_counts(candidate_rows, model_rows, hidden_rows)
    sanitized_rows = make_sanitized_primary_view(model_rows)
    feature_path_rows, sanitized_blocked_feature_path_hits = audit_feature_paths(sanitized_rows)
    blocked_field_rows, model_full_blocked_key_hits, model_feature_blocked_key_hits = audit_blocked_fields(model_rows)
    probe_rows, probe_details = build_probes(model_rows, candidate_rows, hidden_rows)
    distribution_rows = build_distribution_rows(model_rows, hidden_rows)

    critical_high_or_medium = [
        row
        for row in probe_rows
        if row["source"] == "critical_semantic_or_source" and row["risk_level"] in {"high", "medium"}
    ]
    source_confidence_high_or_medium = [
        row for row in critical_high_or_medium if row["probe_name"] in SOURCE_CONFIDENCE_PROBES
    ]
    raw_geometry_high_or_medium = [
        row
        for row in probe_rows
        if row["source"] == "allowed_raw_geometry" and row["risk_level"] in {"high", "medium"}
    ]
    blocked_hidden_high = [
        row for row in probe_rows if row["source"] == "blocked_raw_or_hidden" and row["risk_level"] == "high"
    ]

    errors = build_validation_errors(
        input_errors,
        count_errors,
        sanitized_blocked_feature_path_hits,
        model_feature_blocked_key_hits,
        critical_high_or_medium,
    )
    hard_input_error = any(err.get("scope") in {"input_summary", "input_files", "counts"} for err in errors)
    status = STATUS_ERROR if hard_input_error else (STATUS_BLOCKED if critical_high_or_medium or sanitized_blocked_feature_path_hits or model_feature_blocked_key_hits else STATUS_READY)
    next_todo = (
        "fix_stratum_repair_schema_shortcut_audit_inputs"
        if status == STATUS_ERROR
        else (NEXT_BLOCKED if status == STATUS_BLOCKED else NEXT_READY)
    )
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
    labels = Counter(str(row["target"]["primary_binary"]) for row in model_rows)
    counts = {
        "candidate_rows": len(candidate_rows),
        "family_counts": dict(Counter(row["family"] for row in model_rows)),
        "hidden_manifest_rows": len(hidden_rows),
        "label_counts": dict(sorted(labels.items())),
        "model_safe_rows": len(model_rows),
        "predicate_counts": dict(Counter(row["predicate_label"] for row in model_rows)),
        "retained_exact_strata": len(set(row["stratum_id"] for row in candidate_rows)),
        "sanitized_primary_rows": len(sanitized_rows),
    }
    risk_summary = {
        "blocked_hidden_high_risk": len(blocked_hidden_high),
        "blocked_hidden_high_risk_probe_names": [row["probe_name"] for row in blocked_hidden_high],
        "critical_high_or_medium_probe_names": [row["probe_name"] for row in critical_high_or_medium],
        "critical_high_or_medium_risk": len(critical_high_or_medium),
        "model_feature_blocked_key_hits": model_feature_blocked_key_hits,
        "model_full_blocked_key_hits": model_full_blocked_key_hits,
        "raw_geometry_high_or_medium_probe_names": [row["probe_name"] for row in raw_geometry_high_or_medium],
        "raw_geometry_high_or_medium_risk": len(raw_geometry_high_or_medium),
        "sanitized_blocked_feature_path_hits": sanitized_blocked_feature_path_hits,
        "source_confidence_high_or_medium_probe_names": [row["probe_name"] for row in source_confidence_high_or_medium],
        "source_confidence_high_or_medium_risk": len(source_confidence_high_or_medium),
    }
    summary = {
        "boundary": boundary,
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "candidate_rows": rel_path(args.input_root / "candidate_rows.jsonl"),
            "hidden_manifest": rel_path(args.input_root / "hidden_manifest.jsonl"),
            "input_summary": rel_path(args.input_root / "summary.json"),
            "model_safe_view": rel_path(args.input_root / "model_safe_view.jsonl"),
        },
        "input_status": input_summary.get("status"),
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "path_decision": {
            "learned_smoke_allowed": status == STATUS_READY,
            "next_todo": next_todo,
            "paper_evidence_allowed": False,
            "rationale": (
                "Critical semantic/source shortcut probes remain medium/high; run a path decision before learned smoke."
                if status == STATUS_BLOCKED
                else "Schema and critical shortcut audit passed; plan sanitized-view smoke next."
            ),
            "sanitized_view_smoke_plan_allowed": status == STATUS_READY,
            "selected_path": (
                "stratum_repair_path_decision_after_schema_shortcut_audit"
                if status == STATUS_BLOCKED
                else "write_stratum_repair_sanitized_view_smoke_plan"
            ),
            "status": status,
            "validation_errors": len(errors),
        },
        "risk_summary": risk_summary,
        "schema_version": SCHEMA_VERSION,
        "selected_path": "audit_exact_stratum_repaired_independent_validity_schema_and_shortcuts",
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
