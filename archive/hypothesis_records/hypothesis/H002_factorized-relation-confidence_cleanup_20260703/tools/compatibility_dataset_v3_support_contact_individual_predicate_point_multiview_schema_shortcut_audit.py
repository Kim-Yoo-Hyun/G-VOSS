#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for point/multiview support/contact rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_v1"
)
SMOKE_READY_SCHEMA = (
    "h002_support_contact_individual_predicate_point_multiview_smoke_ready_view_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_ready_for_smoke_plan"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_blocked_shortcut_risk"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_input_errors"
)
NEXT_READY = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan"
NEXT_BLOCKED = (
    "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_path_decision_after_schema_shortcut_audit"
)

EXPECTED_TOTAL_ROWS = 800
EXPECTED_MAIN_ROWS = 640
EXPECTED_DIAGNOSTIC_ROWS = 160
HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75


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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    return output if math.isfinite(output) else None


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
    blocked = [
        "hidden",
        "candidate_role",
        "label_match",
        "queue",
        "machine_hint",
        "matched",
        "geometry_status",
        "p_geom",
        "semantic_rank",
        "semantic_score",
        "source_id",
        "source_path",
        "prediction_id",
        "subgraph_id",
        "scan_id",
        "subject_id",
        "object_id",
        "_path",
        "target_source",
    ]
    if lower.startswith("feature_blocks.q_e_observability."):
        blocked = [fragment for fragment in blocked if fragment not in {"semantic_score", "semantic_rank"}]
    return [fragment for fragment in blocked if fragment in lower]


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
    thresholds = values if len(values) == 1 else [(left + right) / 2.0 for left, right in zip(values, values[1:])]
    if len(thresholds) > 3000:
        step = max(1, len(thresholds) // 3000)
        thresholds = thresholds[::step]
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
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_learned_smoke",
        "trains_new_model",
        "visual_model_input_allowed",
        "source_confidence_in_model_safe_C_e",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in [
        "model_safe_view.jsonl",
        "source_manifest.jsonl",
        "visual_audit_manifest.jsonl",
        "control_manifest.jsonl",
        "feature_stats.json",
        "validation_errors.jsonl",
    ]:
        if not (input_root / name).exists():
            errors.append({"error_type": "missing_input_artifact", "path": rel_path(input_root / name)})
    if (input_root / "validation_errors.jsonl").exists() and (input_root / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_input_validation_errors"})
    counts = summary.get("materialized_counts", {})
    if counts.get("rows") != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "unexpected_total_rows", "actual": counts.get("rows")})
    if counts.get("main_rows") != EXPECTED_MAIN_ROWS:
        errors.append({"error_type": "unexpected_main_rows", "actual": counts.get("main_rows")})
    if counts.get("diagnostic_rows") != EXPECTED_DIAGNOSTIC_ROWS:
        errors.append({"error_type": "unexpected_diagnostic_rows", "actual": counts.get("diagnostic_rows")})
    if counts.get("point_stats_found_rows") != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "point_stats_not_complete", "actual": counts.get("point_stats_found_rows")})
    return errors


def join_rows(
    model_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    visual_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    source_by_id = {row["row_id"]: row for row in source_rows}
    visual_by_id = {row["row_id"]: row for row in visual_rows}
    control_by_id = {row["row_id"]: row for row in control_rows}
    joined: list[dict[str, Any]] = []
    for model in model_rows:
        row_id = model.get("row_id")
        source = source_by_id.get(row_id)
        visual = visual_by_id.get(row_id)
        control = control_by_id.get(row_id)
        if source is None or visual is None or control is None:
            errors.append(
                {
                    "error_type": "missing_manifest_row",
                    "row_id": row_id,
                    "has_source": source is not None,
                    "has_visual": visual is not None,
                    "has_control": control is not None,
                }
            )
            continue
        joined.append({"model": model, "source": source, "visual": visual, "control": control})
    for name, rows, row_map in [
        ("source", source_rows, source_by_id),
        ("visual", visual_rows, visual_by_id),
        ("control", control_rows, control_by_id),
    ]:
        if len(rows) != len(row_map):
            errors.append({"error_type": f"duplicate_{name}_row_ids", "rows": len(rows), "unique": len(row_map)})
    return joined, errors


def main_binary_rows(joined: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    labels: list[int] = []
    for row in joined:
        model = row["model"]
        label = model.get("labels", {}).get("C_e")
        if model.get("model_use") == "main_train_candidate_if_schema_audit_passes" and label in (0, 1):
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


def numeric_feature_paths(model_rows: list[dict[str, Any]], block_name: str) -> list[str]:
    keys: set[str] = set()
    for row in model_rows:
        block = row.get("feature_blocks", {}).get(block_name, {})
        if not isinstance(block, dict):
            continue
        for key, value in block.items():
            if isinstance(value, (int, float, bool)):
                keys.add(key)
    return sorted(keys)


def shortcut_probes(rows: list[dict[str, Any]], labels: list[int]) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    get_m = lambda dotted: (lambda row: nested_get(row["model"], dotted))
    get_s = lambda dotted: (lambda row: nested_get(row["source"], dotted))
    get_v = lambda dotted: (lambda row: nested_get(row["visual"], dotted))

    probes.extend(
        [
            categorical_probe(rows, labels, "model_T_predicate_label", "model_safe_T_e", True, get_m("feature_blocks.T_e.predicate_label"), "predicate-only shortcut check"),
            categorical_probe(rows, labels, "model_T_subject_class", "model_safe_T_e", True, get_m("feature_blocks.T_e.subject_class_text"), "subject class shortcut check"),
            categorical_probe(rows, labels, "model_T_object_class", "model_safe_T_e", True, get_m("feature_blocks.T_e.object_class_text"), "object class shortcut check"),
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
                "model_T_predicate_x_class_pair",
                "model_safe_T_e",
                True,
                lambda row: (
                    f"{nested_get(row['model'], 'feature_blocks.T_e.predicate_label')}::"
                    f"{nested_get(row['model'], 'feature_blocks.T_e.subject_class_text')}->"
                    f"{nested_get(row['model'], 'feature_blocks.T_e.object_class_text')}"
                ),
                "predicate plus class-pair shortcut check",
            ),
            categorical_probe(rows, labels, "model_Q_e_state_code", "model_safe_Q_e", True, get_m("feature_blocks.Q_e_observability.q_e_state_code"), "Q_e state should not be truth label"),
            categorical_probe(rows, labels, "model_Q_e_reason_pattern", "model_safe_Q_e", True, lambda row: tuple(
                nested_get(row["model"], f"feature_blocks.Q_e_observability.{field}") for field in [
                    "q_e_reason_low_crop_score",
                    "q_e_reason_few_cropped_instance_views",
                    "q_e_reason_low_semseg_segment_count",
                    "q_e_reason_low_obb_axis_ratio",
                ]
            ), "Q_e reason-pattern shortcut check"),
            categorical_probe(rows, labels, "hidden_candidate_role", "hidden_target_construction", False, get_s("candidate_role_hidden"), "construction role if leaked"),
            categorical_probe(rows, labels, "hidden_label_match_status", "hidden_target_construction", False, get_s("label_match_status_hidden"), "GT match status if leaked"),
            categorical_probe(rows, labels, "hidden_queue_kind", "hidden_target_construction", False, get_s("queue_kind_hidden"), "HL/LH construction proxy if leaked"),
            categorical_probe(rows, labels, "hidden_rank_band", "hidden_source_confidence", False, get_s("rank_band_hidden"), "rank-band shortcut if leaked"),
            categorical_probe(rows, labels, "hidden_machine_hint", "hidden_target_construction", False, get_s("machine_hint_hidden"), "machine hint if leaked"),
            categorical_probe(rows, labels, "hidden_scan_id", "hidden_identity", False, get_s("scan_id_hidden"), "scan memorization if leaked"),
            categorical_probe(rows, labels, "visual_hidden_q_e_state_plan", "visual_audit_manifest_hidden", False, get_v("q_e_state_plan"), "visual manifest Q_e state is not model input"),
        ]
    )

    sample_model_rows = [row["model"] for row in rows]
    for block in ["G_e_obb_baseline", "G_e_point_pose", "G_e_contact_patch", "Q_e_observability"]:
        for field in numeric_feature_paths(sample_model_rows, block):
            probes.append(
                numeric_probe(
                    rows,
                    labels,
                    f"model_{block}_{field}",
                    f"model_safe_{block}",
                    True,
                    get_m(f"feature_blocks.{block}.{field}"),
                    f"single {block} feature threshold shortcut check",
                )
            )

    for field in [
        "semantic_score_norm_hidden",
        "semantic_score_raw_hidden",
        "semantic_rank_hidden",
        "p_geom_valid_hidden",
        "point_subject_count",
        "point_object_count",
    ]:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"hidden_{field}",
                "hidden_source_or_provenance",
                False,
                get_s(field),
                "hidden source/provenance numeric shortcut if leaked",
            )
        )

    for field in [
        "subject_crop_count",
        "object_crop_count",
        "subject_direct_view_count",
        "object_direct_view_count",
        "subject_max_view_score",
        "object_max_view_score",
        "subject_mean_view_ratio",
        "object_mean_view_ratio",
    ]:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"hidden_visual_{field}",
                "visual_audit_manifest_hidden",
                False,
                get_v(field),
                "visual audit metadata is hidden until wrong-view controls are active",
            )
        )
    return probes


def control_integrity(control_rows: list[dict[str, Any]], row_ids: set[str]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = [
        "wrong_pair_geometry_row_id",
        "shuffled_geometry_global_row_id",
        "shuffled_geometry_within_predicate_row_id",
        "wrong_view_row_id",
        "shuffled_view_within_predicate_or_class_pair_row_id",
    ]
    for row in control_rows:
        row_id = row.get("row_id")
        for field in required:
            target = row.get(field)
            if target not in row_ids:
                errors.append({"row_id": row_id, "error_type": "missing_control_target", "field": field, "target": target})
            if target == row_id:
                errors.append({"row_id": row_id, "error_type": "self_control_target", "field": field})
    return errors


def diagnostic_profile(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    diagnostic = [row for row in joined if row["model"].get("model_use") == "diagnostic_only"]
    for axis, fn in [
        ("labels.C_e", lambda row: nested_get(row["model"], "labels.C_e")),
        ("predicate_label", lambda row: nested_get(row["model"], "feature_blocks.T_e.predicate_label")),
        ("candidate_role_hidden", lambda row: nested_get(row["source"], "candidate_role_hidden")),
        ("label_match_status_hidden", lambda row: nested_get(row["source"], "label_match_status_hidden")),
        ("rank_band_hidden", lambda row: nested_get(row["source"], "rank_band_hidden")),
        ("q_e_state_code", lambda row: nested_get(row["model"], "feature_blocks.Q_e_observability.q_e_state_code")),
    ]:
        counts = Counter(value_key(fn(row)) for row in diagnostic)
        for value, count in sorted(counts.items()):
            rows.append({"subset": "supported_by_diagnostic", "axis": axis, "value": value, "rows": count})
    return rows


def smoke_ready_view(rows: list[dict[str, Any]], labels: list[int]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row, label in zip(rows, labels):
        model = row["model"]
        scan_id = str(row["source"].get("scan_id_hidden", "missing"))
        group_hash = hashlib.sha1(scan_id.encode("utf-8")).hexdigest()[:12]
        out.append(
            {
                "feature_blocks": model["feature_blocks"],
                "row_id": model["row_id"],
                "schema_version": SMOKE_READY_SCHEMA,
                "split": "train",
                "split_metadata": {
                    "cv_group_id": f"scan_{group_hash}",
                    "group_use": "split_only_not_model_feature",
                },
                "target_y": label,
            }
        )
    return out


def build_report(summary: dict[str, Any], probes: list[dict[str, Any]], high_allowed: list[dict[str, Any]]) -> str:
    counts = summary["counts"]
    top_allowed = sorted(
        [probe for probe in probes if probe["allowed_feature"]],
        key=lambda row: max(float(row.get("accuracy", 0.0)), float(row.get("auroc") or 0.0)),
        reverse=True,
    )[:10]
    top_hidden = sorted(
        [probe for probe in probes if not probe["allowed_feature"]],
        key=lambda row: max(float(row.get("accuracy", 0.0)), float(row.get("auroc") or 0.0)),
        reverse=True,
    )[:8]
    lines = [
        "# H002 Support/Contact Individual Predicate Point/Multiview Schema Shortcut Audit",
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
        f"- smoke-ready rows: `{counts['smoke_ready_rows']}`",
        f"- allowed high-risk probes: `{counts['allowed_high_risk_probes']}`",
        f"- allowed medium-risk probes: `{counts['allowed_medium_risk_probes']}`",
        f"- hidden high-risk probes: `{counts['hidden_high_risk_probes']}`",
        f"- schema leakage hits: `{counts['schema_leakage_hits']}`",
        "",
        "## Interpretation",
        "",
        "- `model_safe_view` is checked for hidden/source/GT/provenance leakage.",
        "- Allowed `T_e/G_e/Q_e` probes test whether the new evidence target is too easy before learned smoke.",
        "- Hidden source, construction, and visual-audit probes are reported as risk controls, not model inputs.",
    ]
    if high_allowed:
        lines.append("- Result is blocked because at least one allowed model-safe probe is high-risk.")
    else:
        lines.append("- Result can proceed to smoke planning; learned smoke is still not executed in this step.")
    lines.extend(["", "## Top Allowed Probes", ""])
    for probe in top_allowed:
        lines.append(
            f"- `{probe['probe_name']}`: acc `{probe['accuracy']}`, auroc `{probe.get('auroc', '')}`, risk `{probe['risk_level']}`, source `{probe['source']}`"
        )
    lines.extend(["", "## Top Hidden/Control Probes", ""])
    for probe in top_hidden:
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
    source_rows: list[dict[str, Any]] = []
    visual_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    joined: list[dict[str, Any]] = []
    binary: list[dict[str, Any]] = []
    labels: list[int] = []
    schema_rows: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []

    if not validation_errors:
        model_rows = read_jsonl(args.input_root / "model_safe_view.jsonl")
        source_rows = read_jsonl(args.input_root / "source_manifest.jsonl")
        visual_rows = read_jsonl(args.input_root / "visual_audit_manifest.jsonl")
        control_rows = read_jsonl(args.input_root / "control_manifest.jsonl")
        joined, join_errors = join_rows(model_rows, source_rows, visual_rows, control_rows)
        validation_errors.extend(join_errors)
        validation_errors.extend(control_integrity(control_rows, {str(row.get("row_id")) for row in model_rows}))
        schema_rows = feature_path_audit(model_rows)
        binary, labels = main_binary_rows(joined)
        probes = shortcut_probes(binary, labels)
        diagnostic_rows = diagnostic_profile(joined)
        smoke_rows = smoke_ready_view(binary, labels)

        for name, rows in [
            ("model_rows", model_rows),
            ("source_rows", source_rows),
            ("visual_rows", visual_rows),
            ("control_rows", control_rows),
        ]:
            if len(rows) != EXPECTED_TOTAL_ROWS:
                validation_errors.append({"error_type": f"unexpected_{name}_count", "actual": len(rows), "expected": EXPECTED_TOTAL_ROWS})
        if len(binary) != EXPECTED_MAIN_ROWS:
            validation_errors.append({"error_type": "unexpected_main_binary_rows", "actual": len(binary), "expected": EXPECTED_MAIN_ROWS})
        if Counter(labels) != Counter({0: 320, 1: 320}):
            validation_errors.append({"error_type": "unexpected_main_label_counts", "actual": dict(Counter(labels))})

    schema_leakage_hits = 0
    if schema_rows:
        summary_rows = [row for row in schema_rows if row.get("feature_path") == "__summary__"]
        schema_leakage_hits = int(summary_rows[0].get("hits", 0)) if summary_rows else 0
    allowed_high = [probe for probe in probes if probe["allowed_feature"] and probe["risk_level"] == "high"]
    allowed_medium = [probe for probe in probes if probe["allowed_feature"] and probe["risk_level"] == "medium"]
    hidden_high = [probe for probe in probes if not probe["allowed_feature"] and probe["risk_level"] == "high"]
    critical_rows = allowed_high + (
        [{"probe_name": "schema_feature_path_leakage", "risk_level": "high", "accuracy": 1.0}]
        if schema_leakage_hits
        else []
    )

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
        selected_path = "schema_clean_no_allowed_high_risk_probe_smoke_plan_allowed"
        next_todo = NEXT_READY

    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_new_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_schema_shortcut_audit",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
            "visual_model_input_allowed": False,
        },
        "counts": {
            "allowed_high_risk_probes": len(allowed_high),
            "allowed_medium_risk_probes": len(allowed_medium),
            "diagnostic_rows": EXPECTED_DIAGNOSTIC_ROWS if joined else 0,
            "hidden_high_risk_probes": len(hidden_high),
            "main_binary_rows": len(binary),
            "model_safe_rows": len(model_rows),
            "schema_leakage_hits": schema_leakage_hits,
            "smoke_ready_rows": len(smoke_rows),
            "target_counts": dict(Counter(labels)),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "control_manifest": rel_path(args.input_root / "control_manifest.jsonl"),
            "model_safe_view": rel_path(args.input_root / "model_safe_view.jsonl"),
            "source_manifest": rel_path(args.input_root / "source_manifest.jsonl"),
            "summary": rel_path(args.input_root / "summary.json"),
            "visual_audit_manifest": rel_path(args.input_root / "visual_audit_manifest.jsonl"),
        },
        "next_todo": next_todo,
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "critical_probe_failures": rel_path(args.output_dir / "critical_probe_failures.csv"),
            "diagnostic_profile": rel_path(args.output_dir / "diagnostic_profile.csv"),
            "feature_path_audit": rel_path(args.output_dir / "feature_path_audit.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "shortcut_probe_summary": rel_path(args.output_dir / "shortcut_probe_summary.csv"),
            "smoke_ready_view": rel_path(args.output_dir / "smoke_ready_view.jsonl"),
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
    write_jsonl(args.output_dir / "smoke_ready_view.jsonl", smoke_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(build_report(summary, probes, allowed_high), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
