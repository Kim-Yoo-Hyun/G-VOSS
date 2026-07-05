#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for pose-conditioned support/contact rows."""

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
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_v1"
SMOKE_READY_SCHEMA = "h002_support_contact_pose_conditioned_smoke_ready_view_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_input_errors"
NEXT_TODO = "compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan"

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

EXPECTED_ROWS = 400
EXPECTED_GROUPS = 200
PRIMARY_PREDICATES = {"lying on", "standing on"}
EXPECTED_LABELS = Counter({0: 200, 1: 200})
EXPECTED_PREDICATES = Counter({"lying on": 200, "standing on": 200})

MODEL_FEATURE_ROOT = "feature_blocks"
BLOCKED_FEATURE_PATH_FRAGMENTS = (
    "target",
    "hidden",
    "control",
    "construction",
    "counterfactual",
    "anchor",
    "raw_source",
    "source_prediction_id",
    "source_line_no",
    "geometry_feature_hash",
    "g_e_hash",
    "scan_id",
    "subject_id",
    "object_id",
    "visible_pair",
    "queue",
    "source_predicates",
    "pose_state",
    "hard_surface",
    "p_geom_valid",
    "audit",
    "matched_predicates",
    "compatibility_label",
    "label_rule",
    "label_source",
)

G_E_FIELDS = [
    "abs_surface_gap_subject_bottom_to_object_top",
    "xy_overlap_min_ratio",
    "subject_vertical_extent_ratio",
    "subject_flatness_ratio",
    "subject_major_axis_upness",
    "obb_contact_likelihood_proxy",
    "point_abs_surface_gap_optional",
    "point_contact_candidate_ratio_optional",
    "point_subject_bottom_band_density_optional",
    "point_object_top_band_density_optional",
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
                fields.append(key)
                seen.add(key)
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
        output = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(output) or math.isinf(output):
        return None
    return output


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
    if isinstance(value, list):
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
    if lower.startswith("feature_blocks.g_e_mesh_pose_contact."):
        return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
    if lower.startswith("feature_blocks.q_e_safe."):
        if lower.endswith(".hard_surface_pair_allowed"):
            return []
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
    thresholds = values if len(values) == 1 else [(left + right) / 2.0 for left, right in zip(values, values[1:])]
    best_accuracy = 0.0
    best_rule = ""
    total = len(labels)
    fallback_negative = labels.count(0)
    fallback_positive = labels.count(1)
    for threshold in thresholds:
        for direction in ("ge", "lt"):
            correct = 0
            for row, label in zip(rows, labels):
                value = safe_float(value_fn(row))
                if value is None:
                    correct += int((1 if fallback_positive >= fallback_negative else 0) == label)
                    continue
                pred = 1 if (value >= threshold if direction == "ge" else value < threshold) else 0
                correct += int(pred == label)
            accuracy = correct / total if total else 0.0
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_rule = f"{direction}_{threshold:.8g}"

    return {
        "accuracy": round(best_accuracy, 6),
        "allowed_feature": allowed_feature,
        "best_rule": best_rule,
        "interpretation": interpretation,
        "missing": missing,
        "num_values": len(values),
        "probe_name": probe_name,
        "probe_type": "numeric_threshold",
        "risk_level": risk_level(best_accuracy),
        "source": source,
    }


def combo_value(row: dict[str, Any], fields: list[str]) -> str:
    return " | ".join(value_key(nested_get(row, field)) for field in fields)


def validate_input_summary(summary: dict[str, Any], input_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"scope": "input_summary", "field": "status", "observed": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"scope": "input_summary", "field": "next_todo", "observed": summary.get("next_todo")})
    if int(summary.get("validation_errors", -1)) != 0:
        errors.append({"scope": "input_summary", "field": "validation_errors", "observed": summary.get("validation_errors")})
    path_decision = summary.get("path_decision", {})
    if not path_decision.get("schema_shortcut_audit_allowed"):
        errors.append({"scope": "input_summary", "field": "schema_shortcut_audit_allowed", "observed": path_decision})
    validation_path = input_root / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"scope": "input_validation_errors", "field": "validation_errors.jsonl", "observed": "non_empty"})
    return errors


def make_smoke_ready_view(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    view: list[dict[str, Any]] = []
    for row in candidate_rows:
        view.append(
            {
                "cv_group_id": row["cv_group_id"],
                "example_id": row["row_id"],
                "feature_blocks": {
                    "G_e_mesh_pose_contact": row["G_e_mesh_pose_contact"],
                    "Q_e_safe": row["Q_e_safe"],
                    "T_e": row["T_e"],
                    "Z_e_safe": row["Z_e_safe"],
                },
                "schema_version": SMOKE_READY_SCHEMA,
                "target_y": int(row["labels"]["compatibility_y"]),
            }
        )
    return view


def audit_feature_paths(smoke_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    paths = sorted({path for row in smoke_rows for path in flatten_paths(row.get(MODEL_FEATURE_ROOT, {}), MODEL_FEATURE_ROOT)})
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


def audit_blocked_fields(candidate_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    candidate_paths = sorted({path for row in candidate_rows for path in flatten_paths(row)})
    smoke_paths = sorted({path for row in smoke_rows for path in flatten_paths(row)})
    rows: list[dict[str, Any]] = []
    leakage_count = 0
    for blocked in [
        "controls_hidden",
        "labels",
        "anchor_id",
        "dataset_name",
        "source_dataset",
        "split",
        "row_schema_name",
        "controls_hidden.scan_id",
        "controls_hidden.subject_id",
        "controls_hidden.object_id",
        "controls_hidden.visible_pair",
        "controls_hidden.queue_kinds",
        "controls_hidden.source_predicates",
        "controls_hidden.anchor_pose_state",
        "controls_hidden.G_e_hash",
    ]:
        in_candidate = any(path == blocked or path.startswith(blocked + ".") for path in candidate_paths)
        in_smoke_feature = any(path.startswith(f"{MODEL_FEATURE_ROOT}.") and (path == blocked or path.endswith("." + blocked)) for path in smoke_paths)
        leakage_count += int(in_smoke_feature)
        rows.append(
            {
                "blocked_field": blocked,
                "present_in_candidate_rows": in_candidate,
                "present_in_smoke_feature_blocks": in_smoke_feature,
                "status": "fail" if in_smoke_feature else "pass",
            }
        )
    return rows, leakage_count


def audit_group_integrity(candidate_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_smoke_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_group[str(row.get("cv_group_id"))].append(row)
    for row in smoke_rows:
        by_smoke_group[str(row.get("cv_group_id"))].append(row)

    for group_id, rows in sorted(by_group.items()):
        labels = [int(row["labels"]["compatibility_y"]) for row in rows]
        predicates = sorted(str(row["T_e"]["predicate_label"]) for row in rows)
        g_hashes = {json.dumps(row["G_e_mesh_pose_contact"], sort_keys=True) for row in rows}
        smoke_count = len(by_smoke_group.get(group_id, []))
        status = "pass"
        reasons: list[str] = []
        if len(rows) != 2:
            status = "fail"
            reasons.append("rows_per_group")
        if set(predicates) != PRIMARY_PREDICATES:
            status = "fail"
            reasons.append("predicate_pair")
        if Counter(labels) != Counter({0: 1, 1: 1}):
            status = "fail"
            reasons.append("paired_label")
        if len(g_hashes) != 1:
            status = "fail"
            reasons.append("same_G_e")
        if smoke_count != len(rows):
            status = "fail"
            reasons.append("smoke_count")
        if status == "fail":
            errors.append({"scope": "group_integrity", "group_id": group_id, "reasons": reasons})
        audit_rows.append(
            {
                "cv_group_id": group_id,
                "label_sum": sum(labels),
                "predicates": "|".join(predicates),
                "reason": "|".join(reasons),
                "rows": len(rows),
                "same_G_e_hashes": len(g_hashes),
                "smoke_rows": smoke_count,
                "status": status,
            }
        )

    summary = {
        "groups": len(by_group),
        "groups_passing": sum(1 for row in audit_rows if row["status"] == "pass"),
        "rows_per_group_distribution": dict(Counter(len(rows) for rows in by_group.values())),
    }
    return audit_rows, errors, summary


def build_probes(candidate_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = [int(row["target_y"]) for row in smoke_rows]
    probes: list[dict[str, Any]] = []

    def add_probe(probe: dict[str, Any]) -> None:
        probes.append(probe)

    # Allowed single-field model-feature probes. These should not solve the target alone.
    add_probe(
        categorical_probe(
            smoke_rows,
            labels,
            "predicate_label",
            "allowed_feature",
            True,
            lambda row: nested_get(row, "feature_blocks.T_e.predicate_label"),
            "A single predicate should be balanced across labels; compatibility should need geometry interaction.",
        )
    )
    add_probe(
        categorical_probe(
            smoke_rows,
            labels,
            "subject_class_label",
            "allowed_feature",
            True,
            lambda row: nested_get(row, "feature_blocks.T_e.subject_class_label"),
            "Subject class alone should not determine the target.",
        )
    )
    add_probe(
        categorical_probe(
            smoke_rows,
            labels,
            "object_class_label",
            "allowed_feature",
            True,
            lambda row: nested_get(row, "feature_blocks.T_e.object_class_label"),
            "Object class alone should not determine the target.",
        )
    )
    add_probe(
        categorical_probe(
            smoke_rows,
            labels,
            "subject_object_class_pair",
            "allowed_feature",
            True,
            lambda row: (
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
            "Class pair alone should not determine the target because each anchor has both labels.",
        )
    )
    for field in ["source_score_available", "source_rank_available"]:
        add_probe(
            categorical_probe(
                smoke_rows,
                labels,
                field,
                "allowed_feature",
                True,
                lambda row, field=field: nested_get(row, f"feature_blocks.Z_e_safe.{field}"),
                "Source confidence availability is a safe flag, not a target shortcut.",
            )
        )
    for field in ["semseg_obb_available", "aligned_ply_point_features_available", "point_feature_complete", "hard_surface_pair_allowed"]:
        add_probe(
            categorical_probe(
                smoke_rows,
                labels,
                field,
                "allowed_feature",
                True,
                lambda row, field=field: nested_get(row, f"feature_blocks.Q_e_safe.{field}"),
                "Evidence-quality flag alone should not determine the compatibility target.",
            )
        )
    for field in G_E_FIELDS:
        add_probe(
            numeric_threshold_probe(
                smoke_rows,
                labels,
                field,
                "allowed_feature",
                True,
                lambda row, field=field: nested_get(row, f"feature_blocks.G_e_mesh_pose_contact.{field}"),
                "Single geometry feature alone should not determine the target in a same-G predicate-pair dataset.",
            )
        )

    # Blocked raw/provenance probes. High accuracy here is acceptable only because these fields are excluded.
    raw_probe_specs: list[tuple[str, Callable[[dict[str, Any]], Any], str]] = [
        ("raw_row_id", lambda row: row.get("row_id"), "Unique row ids are blocked metadata."),
        ("raw_anchor_id", lambda row: row.get("anchor_id"), "Anchor ids are blocked group metadata."),
        ("raw_cv_group_id", lambda row: row.get("cv_group_id"), "CV group ids are blocked from feature blocks."),
        ("hidden_G_e_hash", lambda row: nested_get(row, "controls_hidden.G_e_hash"), "Geometry hash is blocked integrity metadata."),
        ("hidden_scan_id", lambda row: nested_get(row, "controls_hidden.scan_id"), "Scan id is blocked provenance."),
        ("hidden_visible_pair", lambda row: nested_get(row, "controls_hidden.visible_pair"), "Visible pair is audit-only provenance."),
        ("hidden_anchor_pose_state", lambda row: nested_get(row, "controls_hidden.anchor_pose_state"), "Pose state defines the label rule and is blocked."),
        ("hidden_queue_kinds", lambda row: nested_get(row, "controls_hidden.queue_kinds"), "Queue kind is construction metadata."),
        ("hidden_source_predicates", lambda row: nested_get(row, "controls_hidden.source_predicates"), "Source predicate set is construction metadata."),
        ("label_source", lambda row: nested_get(row, "labels.label_source"), "Label source is target metadata."),
        ("target_family", lambda row: nested_get(row, "labels.target_family"), "Target family is target metadata."),
        ("target_label_self", lambda row: nested_get(row, "labels.compatibility_y"), "The target itself must never be a feature."),
        (
            "hidden_pose_state_x_predicate",
            lambda row: f"{nested_get(row, 'controls_hidden.anchor_pose_state')}|{nested_get(row, 'T_e.predicate_label')}",
            "The hidden pose-state/predicate pair is the construction rule and must stay blocked.",
        ),
        (
            "hidden_G_hash_x_predicate",
            lambda row: f"{nested_get(row, 'controls_hidden.G_e_hash')}|{nested_get(row, 'T_e.predicate_label')}",
            "Geometry hash plus predicate memorizes rows and must stay blocked.",
        ),
    ]
    raw_labels = [int(nested_get(row, "labels.compatibility_y")) for row in candidate_rows]
    for name, fn, interpretation in raw_probe_specs:
        add_probe(categorical_probe(candidate_rows, raw_labels, name, "blocked_raw", False, fn, interpretation))

    details = probes
    summary_rows = [
        {
            "accuracy": probe["accuracy"],
            "allowed_feature": probe["allowed_feature"],
            "best_rule": probe["best_rule"],
            "num_values": probe.get("num_values", ""),
            "probe_name": probe["probe_name"],
            "probe_type": probe["probe_type"],
            "risk_level": probe["risk_level"],
            "source": probe["source"],
        }
        for probe in probes
    ]
    return summary_rows, details


def validate_counts(candidate_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    labels = Counter(int(row["labels"]["compatibility_y"]) for row in candidate_rows)
    predicates = Counter(str(row["T_e"]["predicate_label"]) for row in candidate_rows)
    if len(candidate_rows) != EXPECTED_ROWS:
        errors.append({"scope": "counts", "field": "candidate_rows", "observed": len(candidate_rows)})
    if len(smoke_rows) != EXPECTED_ROWS:
        errors.append({"scope": "counts", "field": "input_smoke_ready_candidate_view", "observed": len(smoke_rows)})
    if len(hidden_rows) != EXPECTED_ROWS:
        errors.append({"scope": "counts", "field": "hidden_manifest_rows", "observed": len(hidden_rows)})
    if labels != EXPECTED_LABELS:
        errors.append({"scope": "counts", "field": "label_counts", "observed": dict(labels)})
    if predicates != EXPECTED_PREDICATES:
        errors.append({"scope": "counts", "field": "predicate_counts", "observed": dict(predicates)})
    return errors


def build_contract(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_feature_roots": [
            "feature_blocks.T_e",
            "feature_blocks.Z_e_safe",
            "feature_blocks.G_e_mesh_pose_contact",
            "feature_blocks.Q_e_safe",
        ],
        "cv_group_id": "anchor_id carried only as grouped-CV metadata",
        "forbidden_model_feature_fields": list(BLOCKED_FEATURE_PATH_FRAGMENTS),
        "next_todo": NEXT_TODO,
        "schema_version": SMOKE_READY_SCHEMA,
        "target_field": "target_y",
        "train_only": True,
        "usage_boundary": summary["boundary"],
    }


def build_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    risk = summary["risk_summary"]
    outputs = summary["output_paths"]
    return "\n".join(
        [
            "# H002 Support/Contact Pose-Conditioned Schema Shortcut Audit",
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
            f"- smoke_ready_rows: `{counts['smoke_ready_rows']}`",
            f"- groups: `{counts['groups']}`",
            f"- label_counts: `{counts['label_counts']}`",
            f"- predicate_counts: `{counts['predicate_counts']}`",
            "",
            "## Shortcut Result",
            "",
            f"- allowed_feature_high_or_medium_risk: `{risk['allowed_feature_high_or_medium_risk']}`",
            f"- allowed_feature_high_risk: `{risk['allowed_feature_high_risk']}`",
            f"- blocked_raw_high_risk_probes: `{risk['blocked_raw_high_risk_probes']}`",
            f"- blocked_feature_path_hits: `{risk['blocked_feature_path_hits']}`",
            f"- blocked_field_leakage_hits: `{risk['blocked_field_leakage_hits']}`",
            "",
            "Interpretation: single allowed features do not solve the target. High-risk raw probes",
            "are expected for identifiers, target labels, and hidden construction fields, and those",
            "fields are excluded from `feature_blocks`.",
            "",
            "## Outputs",
            "",
            f"- smoke-ready view: `{outputs['smoke_ready_view']}`",
            f"- shortcut probes: `{outputs['shortcut_probes']}`",
            f"- blocked field audit: `{outputs['blocked_field_audit']}`",
            f"- feature path audit: `{outputs['feature_path_audit']}`",
            f"- group integrity audit: `{outputs['group_integrity_audit']}`",
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
    input_smoke_rows = read_jsonl(args.input_root / "smoke_ready_candidate_view.jsonl")
    hidden_rows = read_jsonl(args.input_root / "hidden_manifest.jsonl")

    errors.extend(validate_input_summary(input_summary, args.input_root))
    errors.extend(validate_counts(candidate_rows, input_smoke_rows, hidden_rows))

    smoke_rows = make_smoke_ready_view(candidate_rows)
    group_audit_rows, group_errors, group_summary = audit_group_integrity(candidate_rows, smoke_rows)
    errors.extend(group_errors)

    feature_path_rows, blocked_feature_path_hits = audit_feature_paths(smoke_rows)
    blocked_field_rows, blocked_field_leakage_hits = audit_blocked_fields(candidate_rows, smoke_rows)
    probe_rows, probe_details = build_probes(candidate_rows, smoke_rows)

    allowed_high_or_medium = [
        row
        for row in probe_rows
        if row["allowed_feature"] and row["risk_level"] in {"high", "medium"}
    ]
    allowed_high = [row for row in allowed_high_or_medium if row["risk_level"] == "high"]
    blocked_raw_high = [
        row
        for row in probe_rows
        if not row["allowed_feature"] and row["source"] == "blocked_raw" and row["risk_level"] == "high"
    ]

    if blocked_feature_path_hits:
        errors.append({"scope": "feature_path_audit", "field": "blocked_feature_path_hits", "observed": blocked_feature_path_hits})
    if blocked_field_leakage_hits:
        errors.append({"scope": "blocked_field_audit", "field": "blocked_field_leakage_hits", "observed": blocked_field_leakage_hits})
    if allowed_high_or_medium:
        errors.append(
            {
                "scope": "shortcut_probes",
                "field": "allowed_feature_high_or_medium_risk",
                "observed": [row["probe_name"] for row in allowed_high_or_medium],
            }
        )

    output_paths = {
        "blocked_field_audit": args.output_dir / "blocked_field_audit.csv",
        "feature_path_audit": args.output_dir / "feature_path_audit.csv",
        "group_integrity_audit": args.output_dir / "group_integrity_audit.csv",
        "report": args.output_dir / "report.md",
        "shortcut_probe_details": args.output_dir / "shortcut_probe_details.jsonl",
        "shortcut_probes": args.output_dir / "shortcut_probes.csv",
        "smoke_ready_model_view_contract": args.output_dir / "smoke_ready_model_view_contract.json",
        "smoke_ready_view": args.output_dir / "smoke_ready_view.jsonl",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    status = STATUS_ERROR if errors else STATUS_READY
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
    counts = {
        "candidate_rows": len(candidate_rows),
        "groups": group_summary["groups"],
        "hidden_manifest_rows": len(hidden_rows),
        "input_smoke_ready_candidate_rows": len(input_smoke_rows),
        "label_counts": {str(k): v for k, v in sorted(Counter(int(row["labels"]["compatibility_y"]) for row in candidate_rows).items())},
        "predicate_counts": dict(Counter(str(row["T_e"]["predicate_label"]) for row in candidate_rows)),
        "smoke_ready_rows": len(smoke_rows),
    }
    risk_summary = {
        "allowed_feature_high_or_medium_risk": len(allowed_high_or_medium),
        "allowed_feature_high_risk": len(allowed_high),
        "blocked_field_leakage_hits": blocked_field_leakage_hits,
        "blocked_feature_path_hits": blocked_feature_path_hits,
        "blocked_raw_high_risk_probes": len(blocked_raw_high),
        "group_integrity_errors": len(group_errors),
    }
    summary = {
        "boundary": boundary,
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "candidate_rows": rel_path(args.input_root / "candidate_rows.jsonl"),
            "hidden_manifest": rel_path(args.input_root / "hidden_manifest.jsonl"),
            "input_summary": rel_path(args.input_root / "summary.json"),
            "smoke_ready_candidate_view": rel_path(args.input_root / "smoke_ready_candidate_view.jsonl"),
        },
        "input_status": input_summary.get("status"),
        "next_todo": NEXT_TODO,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "path_decision": {
            "learned_smoke_allowed": False,
            "next_todo": NEXT_TODO,
            "paper_evidence_allowed": False,
            "rationale": "Schema and single-field shortcut audit passed; write a sanitized-view smoke plan before learned smoke.",
            "sanitized_view_smoke_plan_allowed": not errors,
            "selected_path": "write_pose_conditioned_support_contact_sanitized_view_smoke_plan",
            "status": status,
            "validation_errors": len(errors),
        },
        "risk_summary": risk_summary,
        "schema_version": SCHEMA_VERSION,
        "selected_path": "audit_schema_and_single_field_shortcuts_before_learned_smoke",
        "smoke_ready_schema": SMOKE_READY_SCHEMA,
        "status": status,
        "validation_errors": len(errors),
    }

    write_jsonl(output_paths["smoke_ready_view"], smoke_rows)
    write_json(output_paths["smoke_ready_model_view_contract"], build_contract(summary))
    write_csv(output_paths["shortcut_probes"], probe_rows)
    write_jsonl(output_paths["shortcut_probe_details"], probe_details)
    write_csv(output_paths["blocked_field_audit"], blocked_field_rows)
    write_csv(output_paths["feature_path_audit"], feature_path_rows)
    write_csv(output_paths["group_integrity_audit"], group_audit_rows)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
