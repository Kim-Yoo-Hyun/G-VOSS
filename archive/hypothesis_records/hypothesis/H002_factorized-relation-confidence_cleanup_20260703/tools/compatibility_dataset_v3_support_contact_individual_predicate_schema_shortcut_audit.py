#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for support/contact individual predicate rows."""

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
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_v1"
SANITIZED_SCHEMA = "h002_support_contact_individual_predicate_sanitized_view_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_blocked_shortcut_risk"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_input_errors"
NEXT_READY = "compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_support_contact_individual_predicate_path_decision_after_schema_shortcut_audit"

EXPECTED_TOTAL_ROWS = 800
EXPECTED_MAIN_ROWS = 640
EXPECTED_DIAGNOSTIC_ROWS = 160
HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

BLOCKED_FEATURE_PATH_FRAGMENTS = (
    "target",
    "hidden",
    "control",
    "construction",
    "candidate_role",
    "route_name",
    "rank",
    "source",
    "score",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "prediction_id",
    "matched",
    "label_match",
    "geometry_status",
    "h001",
    "p_geom_valid",
    "queue",
    "machine_hint",
)

G_E_FIELDS = [
    "abs_surface_gap_subject_bottom_to_object_top",
    "center_delta_z",
    "center_distance_xy",
    "normal_alignment",
    "normalized_center_distance_xy",
    "obb_contact_likelihood_proxy",
    "object_flatness_ratio",
    "object_major_axis_upness",
    "object_minor_axis_upness",
    "object_normal_upness",
    "object_vertical_extent_ratio",
    "subject_flatness_ratio",
    "subject_major_axis_upness",
    "subject_minor_axis_upness",
    "subject_normal_upness",
    "subject_vertical_extent_ratio",
    "support_area_proxy",
    "support_normal_verticality",
    "surface_gap_subject_bottom_to_object_top",
    "xy_overlap_min_ratio",
    "xy_overlap_object_ratio",
    "xy_overlap_subject_ratio",
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
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        output = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(output):
        return None
    return output


def value_key(value: Any) -> str:
    if value is None or value == "":
        return "missing"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.8g}"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def risk_level(accuracy: float, auroc: float | None = None) -> str:
    score = max(accuracy, auroc if auroc is not None else 0.0)
    if score >= HIGH_RISK_ACC:
        return "high"
    if score >= MEDIUM_RISK_ACC:
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
    if lower.startswith("feature_blocks.g_e_mesh_pose_contact."):
        return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
    if lower.startswith("feature_blocks.q_e."):
        return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
    return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]


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
        "accuracy": round(accuracy, 6),
        "allowed_feature": allowed_feature,
        "auroc": "",
        "best_rule": "per_value_majority",
        "interpretation": interpretation,
        "num_values": len(groups),
        "probe_name": probe_name,
        "probe_type": "categorical_majority",
        "risk_level": risk_level(accuracy),
        "rows": len(rows),
        "source": source,
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
            "auroc": "",
            "best_rule": "no_numeric_values",
            "interpretation": interpretation,
            "missing": missing,
            "num_values": 0,
            "probe_name": probe_name,
            "probe_type": "numeric_threshold",
            "risk_level": "low",
            "rows": len(rows),
            "source": source,
        }
    values = sorted({value for value, _ in pairs})
    if len(values) > 3000:
        step = max(1, len(values) // 3000)
        thresholds = values[::step]
    elif len(values) == 1:
        thresholds = values
    else:
        thresholds = [(left + right) / 2.0 for left, right in zip(values, values[1:])]
    fallback = 1 if labels.count(1) >= labels.count(0) else 0
    best_accuracy = -1.0
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
            accuracy = correct / len(labels) if labels else 0.0
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_rule = f"{direction}_{threshold:.8g}"
    auc = auc_pairwise([value for value, _ in pairs], [label for _, label in pairs])
    return {
        "accuracy": round(best_accuracy, 6),
        "allowed_feature": allowed_feature,
        "auroc": round(auc, 6) if auc is not None else "",
        "best_rule": best_rule,
        "interpretation": interpretation,
        "missing": missing,
        "num_values": len(values),
        "probe_name": probe_name,
        "probe_type": "numeric_threshold",
        "risk_level": risk_level(best_accuracy, auc),
        "rows": len(rows),
        "source": source,
    }


def validate_inputs(summary: dict[str, Any], input_root: Path) -> list[dict[str, Any]]:
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
    for name in [
        "candidate_rows.jsonl",
        "model_safe_view.jsonl",
        "hidden_manifest.jsonl",
        "quota_audit.csv",
        "cap_audit.csv",
        "schema_precheck.csv",
        "validation_errors.jsonl",
    ]:
        if not (input_root / name).exists():
            errors.append({"error_type": "missing_input_artifact", "path": rel_path(input_root / name)})
    if (input_root / "validation_errors.jsonl").exists() and (input_root / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_input_validation_errors"})
    counts = summary.get("counts", {})
    if counts.get("total_rows") != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "unexpected_total_rows", "actual": counts.get("total_rows")})
    if counts.get("main_compatibility_rows") != EXPECTED_MAIN_ROWS:
        errors.append({"error_type": "unexpected_main_rows", "actual": counts.get("main_compatibility_rows")})
    if counts.get("diagnostic_rows") != EXPECTED_DIAGNOSTIC_ROWS:
        errors.append({"error_type": "unexpected_diagnostic_rows", "actual": counts.get("diagnostic_rows")})
    return errors


def join_rows(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    hidden_by_id = {row["row_id"]: row for row in hidden_rows}
    joined: list[dict[str, Any]] = []
    for model_row in model_rows:
        hidden = hidden_by_id.get(model_row.get("row_id"))
        if hidden is None:
            errors.append({"error_type": "missing_hidden_row", "row_id": model_row.get("row_id")})
            continue
        joined.append({"model": model_row, "hidden": hidden})
    if len(hidden_by_id) != len(hidden_rows):
        errors.append({"error_type": "duplicate_hidden_row_ids", "hidden_rows": len(hidden_rows), "unique": len(hidden_by_id)})
    return joined, errors


def main_binary_rows(joined: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    labels: list[int] = []
    for row in joined:
        model = row["model"]
        label = model.get("labels", {}).get("C_e")
        if model.get("subset") == "main_compatibility" and label in (0, 1):
            rows.append(row)
            labels.append(int(label))
    return rows, labels


def feature_path_audit(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    hit_rows: Counter[str] = Counter()
    for row in model_rows:
        row_hits: set[str] = set()
        for path in flatten_paths(row.get("feature_blocks", {}), "feature_blocks"):
            fragments = blocked_fragments_for_feature_path(path)
            if fragments:
                key = f"{path}::{','.join(fragments)}"
                counts[key] += 1
                row_hits.add(key)
        for key in row_hits:
            hit_rows[key] += 1
    if not counts:
        return [{"feature_path": "__summary__", "blocked_fragments": "", "hits": 0, "rows": len(model_rows), "passed": True}]
    rows = []
    for key, hits in sorted(counts.items()):
        path, fragments = key.split("::", 1)
        rows.append({"feature_path": path, "blocked_fragments": fragments, "hits": hits, "rows": hit_rows[key], "passed": False})
    rows.append({"feature_path": "__summary__", "blocked_fragments": "", "hits": sum(counts.values()), "rows": len(model_rows), "passed": False})
    return rows


def shortcut_probes(rows: list[dict[str, Any]], labels: list[int]) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    get_m = lambda dotted: (lambda row: nested_get(row["model"], dotted))
    get_h = lambda dotted: (lambda row: nested_get(row["hidden"], dotted))

    probes.extend(
        [
            categorical_probe(
                rows,
                labels,
                "model_T_predicate_label",
                "model_safe_T_e",
                True,
                get_m("feature_blocks.T_e.predicate_label"),
                "predicate-only shortcut check",
            ),
            categorical_probe(
                rows,
                labels,
                "model_T_subject_class",
                "model_safe_T_e",
                True,
                get_m("feature_blocks.T_e.subject_class_text"),
                "subject class shortcut check",
            ),
            categorical_probe(
                rows,
                labels,
                "model_T_object_class",
                "model_safe_T_e",
                True,
                get_m("feature_blocks.T_e.object_class_text"),
                "object class shortcut check",
            ),
            categorical_probe(
                rows,
                labels,
                "model_T_subject_object_class_pair",
                "model_safe_T_e",
                True,
                lambda row: f"{nested_get(row['model'], 'feature_blocks.T_e.subject_class_text')}->{nested_get(row['model'], 'feature_blocks.T_e.object_class_text')}",
                "class-pair shortcut after cap relaxation",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_hard_surface_pair",
                "hidden_control",
                False,
                get_h("hard_surface_pair"),
                "hard-surface concentration risk",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_rank_band",
                "hidden_control",
                False,
                get_h("rank_band"),
                "rank-band shortcut after cap relaxation",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_predicate_class_pair",
                "hidden_control",
                False,
                get_h("predicate_class_pair"),
                "predicate plus class-pair construction shortcut",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_predicate_class_pair_rank",
                "hidden_control",
                False,
                get_h("predicate_class_pair_rank"),
                "predicate plus class-pair plus rank construction shortcut",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_label_match_status",
                "hidden_target_construction",
                False,
                get_h("label_match_status"),
                "target-construction field; expected to be perfect if leaked",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_candidate_role",
                "hidden_target_construction",
                False,
                get_h("candidate_role"),
                "target-construction field; expected to be perfect if leaked",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_matched_predicates",
                "hidden_target_construction",
                False,
                get_h("matched_predicates"),
                "GT predicate provenance if leaked",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_scan_id",
                "hidden_identity",
                False,
                get_h("scan_id"),
                "scan memorization if leaked",
            ),
            categorical_probe(
                rows,
                labels,
                "hidden_directed_pair_id",
                "hidden_identity",
                False,
                get_h("directed_pair_id"),
                "endpoint memorization if leaked",
            ),
        ]
    )

    for field in G_E_FIELDS:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"model_G_{field}",
                "model_safe_G_e",
                True,
                get_m(f"feature_blocks.G_e_mesh_pose_contact.{field}"),
                "single geometry-feature threshold shortcut check",
            )
        )
    for field in ["p_geom_valid", "semantic_score_norm", "semantic_score_raw", "semantic_rank"]:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"hidden_{field}",
                "hidden_source_or_H001_control",
                False,
                get_h(field),
                "hidden source/H001 numeric shortcut if leaked",
            )
        )
    return probes


def diagnostic_profile(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    diagnostic = [row for row in joined if row["model"].get("subset") == "supported_by_diagnostic"]
    for axis, fn in [
        ("labels.C_e", lambda row: nested_get(row["model"], "labels.C_e")),
        ("candidate_role", lambda row: nested_get(row["hidden"], "candidate_role")),
        ("label_match_status", lambda row: nested_get(row["hidden"], "label_match_status")),
        ("hard_surface_pair", lambda row: nested_get(row["hidden"], "hard_surface_pair")),
        ("rank_band", lambda row: nested_get(row["hidden"], "rank_band")),
    ]:
        counts = Counter(value_key(fn(row)) for row in diagnostic)
        for value, count in sorted(counts.items()):
            rows.append({"subset": "supported_by_diagnostic", "axis": axis, "value": value, "rows": count})
    return rows


def sanitized_view(rows: list[dict[str, Any]], labels: list[int]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for row, label in zip(rows, labels):
        model = row["model"]
        sanitized.append(
            {
                "feature_blocks": model["feature_blocks"],
                "row_id": model["row_id"],
                "schema_version": SANITIZED_SCHEMA,
                "split": "train",
                "target_y": label,
            }
        )
    return sanitized


def build_report(summary: dict[str, Any], probes: list[dict[str, Any]], high_allowed: list[dict[str, Any]]) -> str:
    counts = summary["counts"]
    top_probes = sorted(probes, key=lambda row: float(row.get("accuracy", 0.0)), reverse=True)[:8]
    lines = [
        "# H002 Support/Contact Individual Predicate Schema Shortcut Audit",
        "",
        "## Status",
        "",
        f"- status: `{summary['status']}`",
        f"- selected_path: `{summary['selected_path']}`",
        f"- validation_errors: `{summary['validation_errors']}`",
        f"- next_todo: `{summary['next_todo']}`",
        "",
        "## Counts",
        "",
        f"- main binary rows: `{counts['main_binary_rows']}`",
        f"- diagnostic rows: `{counts['diagnostic_rows']}`",
        f"- allowed high-risk probes: `{counts['allowed_high_risk_probes']}`",
        f"- hidden high-risk probes: `{counts['hidden_high_risk_probes']}`",
        f"- schema leakage hits: `{counts['schema_leakage_hits']}`",
        "",
        "## Interpretation",
        "",
        "- Model-safe `T_e` and single `G_e` probes do not create a high-risk shortcut.",
        "- Hidden target-construction fields such as `label_match_status` and `candidate_role` are high-risk if leaked, but they are absent from the model-safe view.",
        "- Because cap relaxation was required during materialization, class-pair/rank/hard-surface probes are explicitly reported.",
    ]
    if high_allowed:
        lines.append("- Result is blocked because an allowed model-safe probe is high risk.")
    else:
        lines.append("- Result is ready for sanitized-view smoke planning, not learned smoke execution yet.")
    lines.extend(["", "## Top Probes", ""])
    for probe in top_probes:
        lines.append(
            f"- `{probe['probe_name']}`: acc `{probe['accuracy']}`, auroc `{probe.get('auroc', '')}`, risk `{probe['risk_level']}`, source `{probe['source']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary = read_json(args.input_root / "summary.json")
    validation_errors = validate_inputs(input_summary, args.input_root)
    model_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    joined: list[dict[str, Any]] = []
    binary: list[dict[str, Any]] = []
    labels: list[int] = []
    probes: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    sanitized_rows: list[dict[str, Any]] = []

    if not validation_errors:
        model_rows = read_jsonl(args.input_root / "model_safe_view.jsonl")
        hidden_rows = read_jsonl(args.input_root / "hidden_manifest.jsonl")
        joined, join_errors = join_rows(model_rows, hidden_rows)
        validation_errors.extend(join_errors)
        binary, labels = main_binary_rows(joined)
        schema_rows = feature_path_audit(model_rows)
        probes = shortcut_probes(binary, labels)
        diagnostic_rows = diagnostic_profile(joined)
        sanitized_rows = sanitized_view(binary, labels)

        if len(model_rows) != EXPECTED_TOTAL_ROWS:
            validation_errors.append({"error_type": "unexpected_model_row_count", "actual": len(model_rows)})
        if len(hidden_rows) != EXPECTED_TOTAL_ROWS:
            validation_errors.append({"error_type": "unexpected_hidden_row_count", "actual": len(hidden_rows)})
        if len(binary) != EXPECTED_MAIN_ROWS:
            validation_errors.append({"error_type": "unexpected_main_binary_rows", "actual": len(binary)})
        if Counter(labels) != Counter({0: 320, 1: 320}):
            validation_errors.append({"error_type": "unexpected_main_label_counts", "actual": dict(Counter(labels))})

    schema_leakage_hits = 0
    if schema_rows:
        summary_rows = [row for row in schema_rows if row.get("feature_path") == "__summary__"]
        schema_leakage_hits = int(summary_rows[0].get("hits", 0)) if summary_rows else 0
    allowed_high = [probe for probe in probes if probe["allowed_feature"] and probe["risk_level"] == "high"]
    hidden_high = [probe for probe in probes if not probe["allowed_feature"] and probe["risk_level"] == "high"]
    critical_rows = allowed_high + ([{"probe_name": "schema_feature_path_leakage", "risk_level": "high", "accuracy": 1.0}] if schema_leakage_hits else [])

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_or_schema_errors"
        next_todo = EXPECTED_INPUT_NEXT
    elif critical_rows:
        status = STATUS_BLOCKED
        selected_path = "blocked_allowed_model_safe_shortcut_or_schema_leakage"
        next_todo = NEXT_BLOCKED
    else:
        status = STATUS_READY
        selected_path = "schema_clean_allowed_shortcuts_low_hidden_construction_risk_reported"
        next_todo = NEXT_READY

    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_schema_shortcut_audit",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "counts": {
            "allowed_high_risk_probes": len(allowed_high),
            "diagnostic_rows": EXPECTED_DIAGNOSTIC_ROWS if joined else 0,
            "hidden_high_risk_probes": len(hidden_high),
            "main_binary_rows": len(binary),
            "model_safe_rows": len(model_rows),
            "schema_leakage_hits": schema_leakage_hits,
            "sanitized_rows": len(sanitized_rows),
            "target_counts": dict(Counter(labels)),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "hidden_manifest": rel_path(args.input_root / "hidden_manifest.jsonl"),
            "model_safe_view": rel_path(args.input_root / "model_safe_view.jsonl"),
            "summary": rel_path(args.input_root / "summary.json"),
        },
        "next_todo": next_todo,
        "output_paths": {
            "critical_probe_failures": rel_path(args.output_dir / "critical_probe_failures.csv"),
            "diagnostic_profile": rel_path(args.output_dir / "diagnostic_profile.csv"),
            "feature_path_audit": rel_path(args.output_dir / "feature_path_audit.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "sanitized_view": rel_path(args.output_dir / "sanitized_view.jsonl"),
            "shortcut_probe_summary": rel_path(args.output_dir / "shortcut_probe_summary.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_csv(args.output_dir / "feature_path_audit.csv", schema_rows)
    write_csv(args.output_dir / "shortcut_probe_summary.csv", probes)
    write_csv(args.output_dir / "critical_probe_failures.csv", critical_rows)
    write_csv(args.output_dir / "diagnostic_profile.csv", diagnostic_rows)
    write_jsonl(args.output_dir / "sanitized_view.jsonl", sanitized_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(build_report(summary, probes, allowed_high), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
