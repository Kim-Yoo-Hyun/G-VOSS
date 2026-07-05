#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for H002 compatibility dataset v3."""

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

DEFAULT_INPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_candidate_materialization"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_schema_shortcut_audit"

EXPECTED_INPUT_STATUS = "h002_compatibility_dataset_v3_candidate_materialization_ready_for_schema_shortcut_audit"
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_schema_shortcut_audit_v1"
SMOKE_READY_SCHEMA = "h002_compatibility_dataset_v3_smoke_ready_view_v1"
STATUS_READY = "h002_compatibility_dataset_v3_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
STATUS_ERROR = "h002_compatibility_dataset_v3_schema_shortcut_audit_input_errors"
NEXT_TODO = "compatibility_dataset_v3_sanitized_view_smoke_plan"

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

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
    "geometry_group",
    "row_id",
    "cv_group",
    "positive_predicate",
    "direction_bucket",
    "visible_pair",
    "endpoint_state",
    "p_geom_valid",
    "audit",
    "matched_predicates",
    "compatibility_label",
    "label_rule",
    "label_margin",
)

NUMERIC_G_FIELDS_TO_PROBE = [
    "center_delta_z_m",
    "abs_center_delta_z_m",
    "normalized_center_delta_z",
    "subject_center_z",
    "object_center_z",
    "subject_top_z",
    "subject_bottom_z",
    "object_top_z",
    "object_bottom_z",
    "distance_xy_m",
    "distance_3d_m",
    "normalized_distance_xy",
    "bbox_iou_xy",
    "projected_overlap_max",
    "projected_subject_overlap_ratio",
    "projected_object_overlap_ratio",
    "vertical_gap_subject_on_object",
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
                fields.append(key)
                seen.add(key)
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
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
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(flatten_paths(item, child))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def blocked_fragments_for_feature_path(path: str) -> list[str]:
    lower = path.lower()
    if lower.startswith("feature_blocks.t_e."):
        # predicate_label and class_label are semantic-content fields in T_e, not target labels.
        return []
    if lower.startswith("feature_blocks.z_e_safe."):
        return []
    if lower.startswith("feature_blocks.q_e_safe."):
        return []
    if lower.startswith("feature_blocks.g_e_numeric."):
        if lower.endswith(".geometry_feature_hash") or "p_geom_valid" in lower:
            return [fragment for fragment in BLOCKED_FEATURE_PATH_FRAGMENTS if fragment in lower]
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
        "allowed_feature": allowed_feature,
        "probe_type": "categorical_majority",
        "accuracy": round(accuracy, 6),
        "risk_level": risk_level(accuracy),
        "num_values": len(groups),
        "best_rule": "per_value_majority",
        "interpretation": interpretation,
        "majority_by_value": majority_by_value,
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
            "probe_name": probe_name,
            "source": source,
            "allowed_feature": allowed_feature,
            "probe_type": "numeric_threshold",
            "accuracy": 0.0,
            "risk_level": "low",
            "num_values": 0,
            "missing": missing,
            "best_rule": "no_numeric_values",
            "interpretation": interpretation,
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
        "source": source,
        "allowed_feature": allowed_feature,
        "probe_type": "numeric_threshold",
        "accuracy": round(best_acc, 6),
        "risk_level": risk_level(best_acc),
        "num_values": len(values),
        "missing": missing,
        "best_rule": best_rule,
        "interpretation": interpretation,
    }


def compact_probe(probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "probe_name": probe["probe_name"],
        "source": probe["source"],
        "allowed_feature": probe["allowed_feature"],
        "probe_type": probe["probe_type"],
        "accuracy": probe["accuracy"],
        "risk_level": probe["risk_level"],
        "num_values": probe.get("num_values"),
        "missing": probe.get("missing"),
        "best_rule": probe.get("best_rule"),
        "interpretation": probe["interpretation"],
    }


def validate_inputs(summary: dict[str, Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors", "actual": summary.get("validation_errors")})
    for name, path in paths.items():
        if not path.exists():
            errors.append({"error_type": "missing_input_file", "name": name, "path": rel_path(path)})
    return errors


def make_smoke_ready_view(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        g_numeric = {
            key: value
            for key, value in row["G_e_numeric"].items()
            if key != "geometry_feature_hash"
        }
        output.append(
            {
                "schema_version": SMOKE_READY_SCHEMA,
                "example_id": row["row_id"],
                "cv_group_id": row["geometry_group_id"],
                "target_y": row["labels"]["compatibility_label"],
                "target_name": "C_e_predicate_geometry_compatibility",
                "feature_blocks": {
                    "T_e": row["T_e"],
                    "Z_e_safe": row["Z_e_safe"],
                    "G_e_numeric": g_numeric,
                    "Q_e_safe": row["Q_e_safe"],
                },
            }
        )
    return output


def feature_path_audit(smoke_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for smoke_row in smoke_rows:
        for path in flatten_paths(smoke_row.get("feature_blocks", {}), "feature_blocks"):
            hits = blocked_fragments_for_feature_path(path)
            row = {
                "example_id": smoke_row.get("example_id"),
                "feature_path": path,
                "blocked_fragments": ";".join(hits),
                "feature_allowed": not hits,
            }
            rows.append(row)
            if hits:
                errors.append({"error_type": "blocked_feature_path_in_smoke_ready_view", **row})
    return rows, errors


def blocked_field_audit(candidate_rows: list[dict[str, Any]], sanitized_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [
        {
            "artifact": "candidate_rows",
            "path": "labels",
            "role": "label_only",
            "present_rows": sum(1 for row in candidate_rows if "labels" in row),
            "allowed_in_artifact": True,
            "allowed_as_model_feature": False,
        },
        {
            "artifact": "candidate_rows",
            "path": "controls_hidden",
            "role": "audit_only",
            "present_rows": sum(1 for row in candidate_rows if "controls_hidden" in row),
            "allowed_in_artifact": True,
            "allowed_as_model_feature": False,
        },
        {
            "artifact": "sanitized_model_view",
            "path": "G_e_numeric.geometry_feature_hash",
            "role": "group_integrity_identifier",
            "present_rows": sum(1 for row in sanitized_rows if nested_get(row, "G_e_numeric.geometry_feature_hash") is not None),
            "allowed_in_artifact": True,
            "allowed_as_model_feature": False,
        },
        {
            "artifact": "smoke_ready_view",
            "path": "feature_blocks.G_e_numeric.geometry_feature_hash",
            "role": "blocked_identifier",
            "present_rows": sum(1 for row in smoke_rows if nested_get(row, "feature_blocks.G_e_numeric.geometry_feature_hash") is not None),
            "allowed_in_artifact": False,
            "allowed_as_model_feature": False,
        },
        {
            "artifact": "smoke_ready_view",
            "path": "feature_blocks.controls_hidden",
            "role": "blocked_hidden_controls",
            "present_rows": sum(1 for row in smoke_rows if nested_get(row, "feature_blocks.controls_hidden") is not None),
            "allowed_in_artifact": False,
            "allowed_as_model_feature": False,
        },
        {
            "artifact": "smoke_ready_view",
            "path": "feature_blocks.labels",
            "role": "blocked_labels",
            "present_rows": sum(1 for row in smoke_rows if nested_get(row, "feature_blocks.labels") is not None),
            "allowed_in_artifact": False,
            "allowed_as_model_feature": False,
        },
    ]
    for row in checks:
        if row["allowed_in_artifact"]:
            row["status"] = "present_but_blocked_from_model" if row["present_rows"] else "missing"
        else:
            row["status"] = "pass_absent" if row["present_rows"] == 0 else "fail_present"
    return checks


def group_integrity_audit(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_group[row["geometry_group_id"]].append(row)
    rows = []
    for group_id, group_rows in sorted(by_group.items()):
        labels = [row["labels"]["compatibility_label"] for row in group_rows]
        predicates = [row["T_e"]["predicate_label"] for row in group_rows]
        hashes = {row["G_e_numeric"]["geometry_feature_hash"] for row in group_rows}
        rows.append(
            {
                "geometry_group_id": group_id,
                "rows": len(group_rows),
                "label_sum": sum(labels),
                "predicates": ";".join(sorted(predicates)),
                "geometry_hashes": len(hashes),
                "same_geometry_hash_pass": len(hashes) == 1,
                "one_positive_one_negative_pass": sorted(labels) == [0, 1],
                "higher_lower_predicates_pass": set(predicates) == {"higher than", "lower than"},
            }
        )
    return rows


def build_probes(candidate_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = [int(row["target_y"]) for row in smoke_rows]
    probes: list[dict[str, Any]] = []
    probes.extend(
        [
            categorical_probe(
                smoke_rows,
                labels,
                "predicate_label",
                "T_e",
                True,
                lambda row: nested_get(row, "feature_blocks.T_e.predicate_label"),
                "Allowed semantic predicate field; should be balanced by v3 construction.",
            ),
            categorical_probe(
                smoke_rows,
                labels,
                "subject_label",
                "T_e",
                True,
                lambda row: nested_get(row, "feature_blocks.T_e.subject_class_label"),
                "Allowed object-class semantic field; should not solve target alone.",
            ),
            categorical_probe(
                smoke_rows,
                labels,
                "object_label",
                "T_e",
                True,
                lambda row: nested_get(row, "feature_blocks.T_e.object_class_label"),
                "Allowed object-class semantic field; should not solve target alone.",
            ),
            categorical_probe(
                smoke_rows,
                labels,
                "subject_object_text",
                "T_e",
                True,
                lambda row: nested_get(row, "feature_blocks.T_e.subject_object_text"),
                "Allowed semantic pair text; v3 selection should make it label-balanced.",
            ),
            categorical_probe(
                smoke_rows,
                labels,
                "source_rank_band",
                "Z_e_safe",
                True,
                lambda row: nested_get(row, "feature_blocks.Z_e_safe.source_rank_band"),
                "Allowed only for source/factorized baselines; should not shortcut C_e.",
            ),
        ]
    )
    probes.extend(
        [
            numeric_threshold_probe(
                smoke_rows,
                labels,
                "source_score_normalized",
                "Z_e_safe",
                True,
                lambda row: nested_get(row, "feature_blocks.Z_e_safe.source_score_normalized"),
                "Allowed source score for source/factorized baselines, excluded from C_e.",
            ),
            numeric_threshold_probe(
                smoke_rows,
                labels,
                "source_rank",
                "Z_e_safe",
                True,
                lambda row: nested_get(row, "feature_blocks.Z_e_safe.source_rank"),
                "Allowed source rank for source/factorized baselines, excluded from C_e.",
            ),
        ]
    )
    for field in NUMERIC_G_FIELDS_TO_PROBE:
        probes.append(
            numeric_threshold_probe(
                smoke_rows,
                labels,
                f"G_e_numeric.{field}",
                "G_e_numeric",
                True,
                lambda row, name=field: nested_get(row, f"feature_blocks.G_e_numeric.{name}"),
                "Allowed numeric geometry evidence. In same-G paired rows, any single geometry feature should be near chance.",
            )
        )

    raw_labels = [int(row["labels"]["compatibility_label"]) for row in candidate_rows]
    probes.extend(
        [
            categorical_probe(
                candidate_rows,
                raw_labels,
                "raw_row_id",
                "identifier_blocked",
                False,
                lambda row: row.get("row_id"),
                "Unique row identifier; expected to be a perfect blocked shortcut.",
            ),
            categorical_probe(
                candidate_rows,
                raw_labels,
                "raw_geometry_group_id",
                "identifier_blocked",
                False,
                lambda row: row.get("geometry_group_id"),
                "CV grouping key only; must never be a model feature.",
            ),
            categorical_probe(
                candidate_rows,
                raw_labels,
                "hidden_visible_pair",
                "controls_hidden",
                False,
                lambda row: nested_get(row, "controls_hidden.visible_pair"),
                "Hidden control axis retained only for audit.",
            ),
            categorical_probe(
                candidate_rows,
                raw_labels,
                "hidden_predicate_visible_pair",
                "controls_hidden",
                False,
                lambda row: f"{nested_get(row, 'T_e.predicate_label')}|{nested_get(row, 'controls_hidden.visible_pair')}",
                "Hidden control probe for the previously high-risk predicate+visible-pair shortcut.",
            ),
            categorical_probe(
                candidate_rows,
                raw_labels,
                "hidden_direction_bucket",
                "controls_hidden",
                False,
                lambda row: nested_get(row, "controls_hidden.direction_bucket"),
                "Construction direction bucket; audit-only.",
            ),
            categorical_probe(
                candidate_rows,
                raw_labels,
                "hidden_source_prediction_id",
                "controls_hidden",
                False,
                lambda row: nested_get(row, "controls_hidden.source_prediction_id"),
                "Source prediction identifier; expected to be a blocked identifier shortcut.",
            ),
            categorical_probe(
                candidate_rows,
                raw_labels,
                "label_rule_id",
                "labels",
                False,
                lambda row: nested_get(row, "labels.label_rule_id"),
                "Label metadata; label-only field.",
            ),
        ]
    )
    return probes


def probe_rows(probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [compact_probe(probe) for probe in probes]


def validate_audit(
    smoke_rows: list[dict[str, Any]],
    feature_path_errors: list[dict[str, Any]],
    group_rows: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    errors.extend(feature_path_errors)
    if len(smoke_rows) != 400:
        errors.append({"error_type": "unexpected_smoke_ready_rows", "actual": len(smoke_rows), "expected": 400})
    for row in group_rows:
        if not row["same_geometry_hash_pass"] or not row["one_positive_one_negative_pass"] or not row["higher_lower_predicates_pass"]:
            errors.append({"error_type": "group_integrity_failed", **row})
    for row in blocked_rows:
        if row["artifact"] == "smoke_ready_view" and row["status"] == "fail_present":
            errors.append({"error_type": "blocked_field_present_in_smoke_ready_view", **row})
    risky_allowed = [
        compact_probe(probe)
        for probe in probes
        if probe["allowed_feature"] and probe["risk_level"] in {"high", "medium"}
    ]
    for probe in risky_allowed:
        errors.append({"error_type": "allowed_feature_probe_not_low_risk", **probe})
    return errors


def write_report(path: Path, summary: dict[str, Any], probes: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> None:
    allowed_risky = [probe for probe in probes if probe["allowed_feature"] and probe["risk_level"] != "low"]
    blocked_high = [probe for probe in probes if not probe["allowed_feature"] and probe["risk_level"] == "high"]
    blocked_present = [row for row in blocked if row["status"] in {"present_but_blocked_from_model", "fail_present"}]
    lines = [
        "# Compatibility Dataset V3 Schema Shortcut Audit",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_schema_shortcut_audit/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"candidate_rows = {summary['candidate_rows']}",
        f"smoke_ready_rows = {summary['smoke_ready_rows']}",
        f"allowed_feature_high_or_medium_risk = {summary['allowed_feature_high_or_medium_risk']}",
        f"blocked_raw_high_risk_probes = {summary['blocked_raw_high_risk_probes']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "`candidate_rows.jsonl` remains the full audit artifact. It contains labels and hidden controls",
        "by design, so it is not a model input. The audit emits a stricter `smoke_ready_view.jsonl`",
        "where feature blocks contain only `T_e`, `Z_e_safe`, numeric `G_e`, and `Q_e_safe`.",
        "",
        "The previous `geometry_feature_hash` is removed from model features. It is retained only in",
        "group/integrity artifacts.",
        "",
        "## Allowed Feature Probes",
        "",
    ]
    if allowed_risky:
        for probe in allowed_risky:
            lines.append(f"- `{probe['probe_name']}`: {probe['risk_level']} ({probe['accuracy']})")
    else:
        lines.append("- all allowed feature probes are low risk")
    lines.extend(["", "## Blocked Raw Probes", ""])
    if blocked_high:
        for probe in blocked_high[:12]:
            lines.append(f"- `{probe['probe_name']}`: {probe['risk_level']} ({probe['accuracy']})")
    else:
        lines.append("- no blocked raw high-risk probes found")
    lines.extend(["", "## Blocked Field Audit", ""])
    for row in blocked_present:
        lines.append(f"- `{row['artifact']}::{row['path']}` -> {row['status']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- train-only schema and shortcut audit",
            "- no learned smoke",
            "- no validation/test usage",
            "- no paper evidence promotion",
            "- no H001 artifact modification",
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

    paths = {
        "summary": args.input_root / "summary.json",
        "candidate_rows": args.input_root / "candidate_rows.jsonl",
        "sanitized_model_view": args.input_root / "sanitized_model_view.jsonl",
        "model_view_contract": args.input_root / "model_view_contract.json",
    }
    input_summary = read_json(paths["summary"]) if paths["summary"].exists() else {}
    input_errors = validate_inputs(input_summary, paths)

    candidate_rows = read_jsonl(paths["candidate_rows"]) if paths["candidate_rows"].exists() else []
    sanitized_rows = read_jsonl(paths["sanitized_model_view"]) if paths["sanitized_model_view"].exists() else []
    model_view_contract = read_json(paths["model_view_contract"]) if paths["model_view_contract"].exists() else {}
    smoke_rows = make_smoke_ready_view(candidate_rows)
    feature_paths, feature_path_errors = feature_path_audit(smoke_rows)
    blocked_rows = blocked_field_audit(candidate_rows, sanitized_rows, smoke_rows)
    group_rows = group_integrity_audit(candidate_rows)
    probes = build_probes(candidate_rows, smoke_rows)
    audit_errors = validate_audit(smoke_rows, feature_path_errors, group_rows, probes, blocked_rows)
    errors = input_errors + audit_errors

    status = STATUS_READY if not errors else STATUS_ERROR
    allowed_risky = [compact_probe(probe) for probe in probes if probe["allowed_feature"] and probe["risk_level"] in {"high", "medium"}]
    blocked_high = [compact_probe(probe) for probe in probes if not probe["allowed_feature"] and probe["risk_level"] == "high"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO if not errors else "compatibility_dataset_v3_schema_shortcut_audit_repair",
        "input_root": rel_path(args.input_root),
        "output_root": rel_path(args.output_dir),
        "candidate_rows": len(candidate_rows),
        "smoke_ready_rows": len(smoke_rows),
        "group_integrity_rows": len(group_rows),
        "allowed_feature_high_or_medium_risk": len(allowed_risky),
        "blocked_raw_high_risk_probes": len(blocked_high),
        "blocked_raw_high_risk_probe_names": [row["probe_name"] for row in blocked_high],
        "smoke_ready_feature_path_errors": len(feature_path_errors),
        "validation_errors": len(errors),
        "raw_candidate_rows_allowed_as_model_input": False,
        "input_sanitized_model_view_allowed_directly": False,
        "smoke_ready_view_allowed_as_model_input_source": not errors,
        "model_view_contract_input_schema": model_view_contract.get("schema_version"),
        "materializes_dataset": False,
        "runs_learned_smoke": False,
        "paper_evidence_allowed": False,
        "boundary": {
            "schema_shortcut_audit_only": True,
            "train_only": True,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "smoke_ready_view": rel_path(args.output_dir / "smoke_ready_view.jsonl"),
            "smoke_ready_model_view_contract": rel_path(args.output_dir / "smoke_ready_model_view_contract.json"),
            "shortcut_probes": rel_path(args.output_dir / "shortcut_probes.csv"),
            "shortcut_probe_details": rel_path(args.output_dir / "shortcut_probe_details.jsonl"),
            "blocked_field_audit": rel_path(args.output_dir / "blocked_field_audit.csv"),
            "feature_path_audit": rel_path(args.output_dir / "feature_path_audit.csv"),
            "group_integrity_audit": rel_path(args.output_dir / "group_integrity_audit.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    smoke_contract = {
        "schema_version": "h002_v3_smoke_ready_model_view_contract_v1",
        "allowed_model_view_file": "smoke_ready_view.jsonl",
        "target": "target_y",
        "group_key_for_cv_only": "cv_group_id",
        "example_id_metadata_only": "example_id",
        "feature_root": "feature_blocks",
        "primary_view": "compatibility_TG",
        "views": {
            "semantic_only_T": ["feature_blocks.T_e"],
            "source_only_Z_safe": ["feature_blocks.Z_e_safe"],
            "geometry_only_G": ["feature_blocks.G_e_numeric"],
            "compatibility_TG": ["feature_blocks.T_e", "feature_blocks.G_e_numeric"],
            "factorized_sanitized_TZGQ": [
                "feature_blocks.T_e",
                "feature_blocks.Z_e_safe",
                "feature_blocks.G_e_numeric",
                "feature_blocks.Q_e_safe",
            ],
        },
        "blocked_as_features": [
            "example_id",
            "cv_group_id",
            "target_y",
            "target_name",
            "geometry_feature_hash",
            "labels",
            "controls_hidden",
            "row_id",
            "geometry_group_id",
        ],
    }

    write_jsonl(args.output_dir / "smoke_ready_view.jsonl", smoke_rows)
    write_json(args.output_dir / "smoke_ready_model_view_contract.json", smoke_contract)
    write_csv(args.output_dir / "shortcut_probes.csv", probe_rows(probes))
    write_jsonl(args.output_dir / "shortcut_probe_details.jsonl", probes)
    write_csv(args.output_dir / "blocked_field_audit.csv", blocked_rows)
    write_csv(args.output_dir / "feature_path_audit.csv", feature_paths)
    write_csv(args.output_dir / "group_integrity_audit.csv", group_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, probes, blocked_rows)


if __name__ == "__main__":
    main()
