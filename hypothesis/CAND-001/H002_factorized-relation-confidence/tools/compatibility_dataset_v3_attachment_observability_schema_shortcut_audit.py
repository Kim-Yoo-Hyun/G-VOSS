#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for R7 attachment-observability rows."""

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
    / "artifacts/compatibility_dataset_v3_attachment_observability_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_schema_shortcut_audit"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_attachment_observability_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_v1"
SMOKE_READY_SCHEMA = "h002_r7_attachment_observability_smoke_ready_view_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_ready_for_smoke_plan"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_blocked_shortcut_risk"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_input_errors"
NEXT_READY = "compatibility_dataset_v3_attachment_observability_smoke_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit"

EXPECTED_ROWS = 560
EXPECTED_PRIMARY_ROWS = 480
EXPECTED_DIAGNOSTIC_ROWS = 80
EXPECTED_P_OBS = Counter({1: 306, 0: 254})
EXPECTED_P_REL = Counter({0: 246, 1: 60})

HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

FORBIDDEN_MODEL_SAFE_KEYS = {
    "candidate_id",
    "cell_id_hidden",
    "compatibility_binary_target",
    "directed_pair_id",
    "geometry_support_binary_target",
    "label_match_status_hidden",
    "matched_predicates_hidden",
    "object_id",
    "p_geom_valid",
    "p_obs_target",
    "p_rel_observable_target",
    "p_rel_target",
    "packet_id",
    "packet_request_id",
    "prediction_id",
    "primary_relation_binary_target",
    "query_id",
    "query_id_hidden",
    "rank_band_hidden",
    "review_coverage",
    "review_endpoint_identity",
    "review_geometry_support",
    "review_notes",
    "review_relation_reliability",
    "review_uncertainty",
    "scan_id",
    "selection_proxy_role_hidden",
    "selection_route_hidden",
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "source_rank",
    "source_score",
    "subgraph_id",
    "subject_id",
}
FORBIDDEN_MODEL_SAFE_SUBSTRINGS = (
    "_hidden",
    "_target",
    "review_",
    "packet_request",
    "packet_dir",
    "packet_path",
    "query_",
    "source_",
    "scan_id",
    "subject_id",
    "object_id",
    "path",
)


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


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
    feature_source: str,
    allowed_in_model: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
    target_name: str,
    blocker_policy: str,
) -> dict[str, Any]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row, label in zip(rows, labels):
        groups[value_key(value_fn(row))][label] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows) if rows else 0.0
    return {
        "accuracy": round(accuracy, 6),
        "allowed_in_model": allowed_in_model,
        "auroc": "",
        "best_rule": "per_value_majority",
        "blocker_policy": blocker_policy,
        "feature_source": feature_source,
        "interpretation": interpretation,
        "num_values": len(groups),
        "probe_name": probe_name,
        "probe_type": "categorical_majority",
        "risk_level": risk_level(accuracy),
        "rows": len(rows),
        "target_name": target_name,
    }


def numeric_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    probe_name: str,
    feature_source: str,
    allowed_in_model: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
    target_name: str,
    blocker_policy: str,
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
            "allowed_in_model": allowed_in_model,
            "auroc": "",
            "best_rule": "no_numeric_values",
            "blocker_policy": blocker_policy,
            "feature_source": feature_source,
            "interpretation": interpretation,
            "missing": missing,
            "num_values": 0,
            "probe_name": probe_name,
            "probe_type": "numeric_threshold",
            "risk_level": "low",
            "rows": len(rows),
            "target_name": target_name,
        }
    values = sorted({value for value, _ in pairs})
    thresholds = values if len(values) == 1 else [(a + b) / 2.0 for a, b in zip(values, values[1:])]
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
        "allowed_in_model": allowed_in_model,
        "auroc": round(auc, 6) if auc is not None else "",
        "best_rule": best_rule,
        "blocker_policy": blocker_policy,
        "feature_source": feature_source,
        "interpretation": interpretation,
        "missing": missing,
        "num_values": len(values),
        "probe_name": probe_name,
        "probe_type": "numeric_threshold",
        "risk_level": risk_level(best_accuracy, auc),
        "rows": len(rows),
        "target_name": target_name,
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
        "learned_smoke_executed",
        "trains_new_model",
        "runs_model",
        "multi_view_as_raw_model_input",
        "mesh_as_raw_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in [
        "summary.json",
        "source_rows.jsonl",
        "model_safe_view.jsonl",
        "target_manifest.jsonl",
        "hidden_manifest.jsonl",
        "control_manifest.jsonl",
        "schema_audit_inputs.json",
        "validation_errors.jsonl",
    ]:
        path = input_root / name
        if not path.exists():
            errors.append({"error_type": "missing_input_artifact", "path": rel_path(path)})
    if (input_root / "validation_errors.jsonl").exists() and (input_root / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_input_validation_errors"})
    counts = summary.get("counts", {})
    if counts.get("rows") != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_rows", "actual": counts.get("rows")})
    if counts.get("rows_by_route_role", {}).get("primary_observability_then_reliability") != EXPECTED_PRIMARY_ROWS:
        errors.append({"error_type": "unexpected_primary_rows", "actual": counts.get("rows_by_route_role", {})})
    if counts.get("rows_by_route_role", {}).get("diagnostic_observability_then_topology") != EXPECTED_DIAGNOSTIC_ROWS:
        errors.append({"error_type": "unexpected_diagnostic_rows", "actual": counts.get("rows_by_route_role", {})})
    return errors


def schema_leakage_rows(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    hit_count = 0
    for index, row in enumerate(model_rows):
        hits: list[str] = []
        for key in row:
            lower = key.lower()
            if key in FORBIDDEN_MODEL_SAFE_KEYS:
                hits.append(f"exact:{key}")
            for fragment in FORBIDDEN_MODEL_SAFE_SUBSTRINGS:
                if fragment in lower:
                    hits.append(f"fragment:{fragment}:{key}")
        if hits:
            hit_count += len(hits)
            if len(rows) < 50:
                rows.append({"row_index": index, "blocked_hits": ";".join(hits), "passed": False})
    rows.append({"row_index": "__summary__", "blocked_hits": hit_count, "passed": hit_count == 0})
    return rows


def block(row: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key.startswith(prefix)}


def join_rows(
    model_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    joined: list[dict[str, Any]] = []
    if not (len(model_rows) == len(source_rows) == len(target_rows) == len(hidden_rows)):
        errors.append(
            {
                "error_type": "row_count_mismatch",
                "model": len(model_rows),
                "source": len(source_rows),
                "target": len(target_rows),
                "hidden": len(hidden_rows),
            }
        )
        return joined, errors
    seen_uids: set[str] = set()
    for index, (model, source, target, hidden) in enumerate(zip(model_rows, source_rows, target_rows, hidden_rows)):
        row_uid = source.get("row_uid")
        if not row_uid or target.get("row_uid") != row_uid or hidden.get("row_uid") != row_uid:
            errors.append(
                {
                    "error_type": "row_uid_alignment_error",
                    "index": index,
                    "source": row_uid,
                    "target": target.get("row_uid"),
                    "hidden": hidden.get("row_uid"),
                }
            )
            continue
        if row_uid in seen_uids:
            errors.append({"error_type": "duplicate_row_uid", "row_uid": row_uid})
            continue
        seen_uids.add(row_uid)
        joined.append({"hidden": hidden, "model": model, "row_uid": row_uid, "source": source, "target": target})
    return joined, errors


def p_obs_rows(joined: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    labels: list[int] = []
    for row in joined:
        label = row["target"].get("p_obs_target")
        if label in (0, 1):
            rows.append(row)
            labels.append(int(label))
    return rows, labels


def p_rel_rows(joined: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int]]:
    rows: list[dict[str, Any]] = []
    labels: list[int] = []
    for row in joined:
        if row["target"].get("p_rel_observable_usable") is not True:
            continue
        label = row["target"].get("p_rel_observable_target")
        if label in (0, 1):
            rows.append(row)
            labels.append(int(label))
    return rows, labels


def binned(value: Any, bins: tuple[float, ...]) -> str:
    number = safe_float(value)
    if number is None:
        return "missing"
    for threshold in bins:
        if number <= threshold:
            return f"le_{threshold:g}"
    return f"gt_{bins[-1]:g}"


def shortcut_probes(rows: list[dict[str, Any]], labels: list[int], target_name: str) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    m = lambda key: (lambda row: row["model"].get(key))
    h = lambda key: (lambda row: row["hidden"].get(key))
    t = lambda key: (lambda row: row["target"].get(key))

    # Q_e is expected to explain p_obs, but Q_e-only solving p_rel is a shortcut risk.
    q_policy = "expected_for_p_obs" if target_name == "p_obs" else "block_if_high"
    tgq_policy = "block_if_high"

    categorical_specs: list[tuple[str, str, bool, Callable[[dict[str, Any]], Any], str, str]] = [
        ("T_predicate_label", "model_safe_T_e", True, m("t_predicate_label"), "predicate shortcut check", tgq_policy),
        ("T_subject_label", "model_safe_T_e", True, m("t_subject_label"), "subject class shortcut check", tgq_policy),
        ("T_object_label", "model_safe_T_e", True, m("t_object_label"), "object class shortcut check", tgq_policy),
        ("T_subject_object_pair", "model_safe_T_e", True, m("t_subject_object_pair"), "class-pair shortcut check", tgq_policy),
        (
            "T_predicate_x_class_pair",
            "model_safe_T_e",
            True,
            lambda row: f"{row['model'].get('t_predicate_label')}::{row['model'].get('t_subject_object_pair')}",
            "predicate and class-pair shortcut check",
            tgq_policy,
        ),
        ("T_subject_family", "model_safe_T_e", True, m("t_subject_family"), "subject family shortcut check", tgq_policy),
        ("T_object_family", "model_safe_T_e", True, m("t_object_family"), "object family shortcut check", tgq_policy),
        (
            "T_anchor_connector_pattern",
            "model_safe_T_e",
            True,
            lambda row: (row["model"].get("t_object_anchor_surface_label_hint"), row["model"].get("t_endpoint_connector_label_hint")),
            "attachment semantic hint shortcut check",
            tgq_policy,
        ),
        (
            "Q_visual_tier",
            "model_safe_Q_e",
            True,
            m("q_visual_evidence_tier"),
            "observability tier shortcut check",
            q_policy,
        ),
        (
            "Q_covisibility_pattern",
            "model_safe_Q_e",
            True,
            lambda row: (
                row["model"].get("q_same_frame_covisible"),
                row["model"].get("q_same_view_weak"),
                row["model"].get("q_strong_pair_visual_ready"),
            ),
            "co-visibility shortcut check",
            q_policy,
        ),
        (
            "Q_evidence_ready_pattern",
            "model_safe_Q_e",
            True,
            lambda row: (
                row["model"].get("q_mesh_evidence_ready"),
                row["model"].get("q_multiview_evidence_ready"),
                row["model"].get("q_contact_sheet_ready"),
                row["model"].get("q_individual_visual_plus_mesh"),
            ),
            "evidence-ready pattern shortcut check",
            q_policy,
        ),
        (
            "Q_shared_view_bucket",
            "model_safe_Q_e",
            True,
            lambda row: (
                binned(row["model"].get("q_shared_origin_frame_count"), (0, 1, 2, 4)),
                binned(row["model"].get("q_shared_view_rank_count"), (0, 1, 2, 4)),
            ),
            "shared-view bucket shortcut check",
            q_policy,
        ),
        ("hidden_query_id", "hidden_source_construction", False, h("query_id_hidden"), "query construction if leaked", "hidden_report_only"),
        ("hidden_rank_band", "hidden_source_construction", False, h("rank_band_hidden"), "rank band if leaked", "hidden_report_only"),
        ("hidden_selection_proxy", "hidden_source_construction", False, h("selection_proxy_role_hidden"), "selection proxy if leaked", "hidden_report_only"),
        ("hidden_cell_id", "hidden_source_construction", False, h("cell_id_hidden"), "cell id if leaked", "hidden_report_only"),
        ("hidden_label_match_status", "hidden_source_construction", False, h("label_match_status_hidden"), "GT match status if leaked", "hidden_report_only"),
        ("hidden_review_geometry_support", "hidden_review_label", False, h("review_geometry_support"), "review geometry label if leaked", "hidden_report_only"),
        ("hidden_review_reliability", "hidden_review_label", False, h("review_relation_reliability"), "review reliability label if leaked", "hidden_report_only"),
        ("hidden_review_coverage", "hidden_review_label", False, h("review_coverage"), "review coverage label if leaked", "hidden_report_only"),
        ("hidden_scan_id", "hidden_identity", False, h("scan_id"), "scan memorization if leaked", "hidden_report_only"),
        ("target_route_role", "target_manifest", False, t("route_role"), "target route role is not model input", "hidden_report_only"),
    ]
    for suffix, source, allowed, fn, interpretation, policy in categorical_specs:
        probes.append(
            categorical_probe(
                rows,
                labels,
                f"{target_name}:{suffix}",
                source,
                allowed,
                fn,
                interpretation,
                target_name,
                policy,
            )
        )

    for key in sorted(k for k in rows[0]["model"] if k.startswith("g_")) if rows else []:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"{target_name}:G_{key}",
                "model_safe_G_e",
                True,
                m(key),
                "single geometry feature threshold shortcut check",
                target_name,
                tgq_policy,
            )
        )
    for key in sorted(k for k in rows[0]["model"] if k.startswith("q_")) if rows else []:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"{target_name}:Q_{key}",
                "model_safe_Q_e",
                True,
                m(key),
                "single observability feature threshold shortcut check",
                target_name,
                q_policy,
            )
        )
    for key in ["semantic_score_norm_hidden", "semantic_rank_hidden"]:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"{target_name}:hidden_{key}",
                "hidden_source_confidence",
                False,
                h(key),
                "hidden source confidence if leaked",
                target_name,
                "hidden_report_only",
            )
        )
    return probes


def critical_probe_failures(probes: list[dict[str, Any]], schema_hits: int) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if schema_hits:
        failures.append(
            {
                "accuracy": 1.0,
                "auroc": "",
                "blocker": "schema_leakage",
                "reason": "model_safe_view contains hidden/target/provenance fields",
                "target_name": "schema",
            }
        )
    for probe in probes:
        if probe.get("blocker_policy") != "block_if_high":
            continue
        if probe.get("allowed_in_model") is not True:
            continue
        if probe.get("risk_level") != "high":
            continue
        failures.append(
            {
                "accuracy": probe.get("accuracy"),
                "auroc": probe.get("auroc"),
                "blocker": probe.get("probe_name"),
                "reason": "allowed model-safe feature nearly reconstructs target",
                "target_name": probe.get("target_name"),
            }
        )
    return failures


def diagnostic_profile(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subset_name, subset in [
        ("all", joined),
        ("primary", [row for row in joined if row["target"].get("route_role") == "primary_observability_then_reliability"]),
        ("connected_diagnostic", [row for row in joined if row["target"].get("predicate_label") == "connected to"]),
    ]:
        for axis, fn in [
            ("predicate_label", lambda row: row["target"].get("predicate_label")),
            ("p_obs_target", lambda row: row["target"].get("p_obs_target")),
            ("p_rel_observable_target", lambda row: row["target"].get("p_rel_observable_target")),
            ("review_relation_reliability", lambda row: row["hidden"].get("review_relation_reliability")),
            ("review_geometry_support", lambda row: row["hidden"].get("review_geometry_support")),
            ("rank_band_hidden", lambda row: row["hidden"].get("rank_band_hidden")),
            ("q_visual_evidence_tier", lambda row: row["model"].get("q_visual_evidence_tier")),
        ]:
            counts = Counter(value_key(fn(row)) for row in subset)
            for value, count in sorted(counts.items()):
                rows.append({"axis": axis, "rows": count, "subset": subset_name, "value": value})
    return rows


def smoke_ready_view(rows: list[dict[str, Any]], labels: list[int], target_name: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row, label in zip(rows, labels):
        scan_id = str(row["hidden"].get("scan_id", "missing"))
        group_hash = hashlib.sha1(scan_id.encode("utf-8")).hexdigest()[:12]
        model = row["model"]
        output.append(
            {
                "feature_blocks": {
                    "G_e_attachment": block(model, "g_"),
                    "Q_e_observability": block(model, "q_"),
                    "T_e": block(model, "t_"),
                },
                "row_uid": row["row_uid"],
                "schema_version": SMOKE_READY_SCHEMA,
                "split": "train",
                "split_metadata": {
                    "cv_group_id": f"scan_{group_hash}",
                    "group_use": "split_only_not_model_feature",
                    "predicate_label": row["target"].get("predicate_label"),
                    "route_role": row["target"].get("route_role"),
                },
                "target_name": target_name,
                "target_y": label,
            }
        )
    return output


def build_report(
    summary: dict[str, Any],
    probes: list[dict[str, Any]],
    critical: list[dict[str, Any]],
) -> str:
    counts = summary["counts"]
    top_allowed = sorted(
        [probe for probe in probes if probe["allowed_in_model"]],
        key=lambda row: max(float(row.get("accuracy", 0.0)), float(row.get("auroc") or 0.0)),
        reverse=True,
    )[:15]
    top_hidden = sorted(
        [probe for probe in probes if not probe["allowed_in_model"]],
        key=lambda row: max(float(row.get("accuracy", 0.0)), float(row.get("auroc") or 0.0)),
        reverse=True,
    )[:10]
    lines = [
        "# H002 R7 Attachment Observability Schema Shortcut Audit",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Counts",
        "",
        f"- rows: `{counts['rows']}`",
        f"- p_obs rows: `{counts['p_obs_rows']}`",
        f"- p_rel observable rows: `{counts['p_rel_rows']}`",
        f"- p_rel labels: `{counts['p_rel_target_counts']}`",
        f"- schema leakage hits: `{counts['schema_leakage_hits']}`",
        f"- allowed high-risk blockers: `{counts['allowed_high_risk_blockers']}`",
        f"- allowed medium-risk probes: `{counts['allowed_medium_risk_probes']}`",
        f"- hidden high-risk probes: `{counts['hidden_high_risk_probes']}`",
        "",
        "## Interpretation",
        "",
        "- `p_obs` is allowed to depend strongly on `Q_e`; that is the observability head.",
        "- Observable `p_rel` should not be nearly solved by a single allowed `T_e`, `G_e`, or `Q_e` shortcut.",
        "- Hidden review/source/provenance probes are reported as leakage risk controls, not model inputs.",
    ]
    if critical:
        lines.append("- Result is blocked for learned smoke because at least one critical shortcut risk remains.")
    else:
        lines.append("- Schema audit can proceed to smoke planning. Learned smoke was not run in this step.")
    lines.extend(["", "## Critical Failures", ""])
    if critical:
        for row in critical:
            lines.append(
                f"- `{row['blocker']}` on `{row['target_name']}`: acc `{row['accuracy']}`, auroc `{row['auroc']}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Top Allowed Probes", ""])
    for probe in top_allowed:
        lines.append(
            f"- `{probe['probe_name']}`: acc `{probe['accuracy']}`, auroc `{probe.get('auroc', '')}`, risk `{probe['risk_level']}`, policy `{probe['blocker_policy']}`"
        )
    lines.extend(["", "## Top Hidden/Control Probes", ""])
    for probe in top_hidden:
        lines.append(
            f"- `{probe['probe_name']}`: acc `{probe['accuracy']}`, auroc `{probe.get('auroc', '')}`, risk `{probe['risk_level']}`"
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
    target_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    joined: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    p_obs_binary: list[dict[str, Any]] = []
    p_obs_labels: list[int] = []
    p_rel_binary: list[dict[str, Any]] = []
    p_rel_labels: list[int] = []

    if not validation_errors:
        model_rows = read_jsonl(args.input_root / "model_safe_view.jsonl")
        source_rows = read_jsonl(args.input_root / "source_rows.jsonl")
        target_rows = read_jsonl(args.input_root / "target_manifest.jsonl")
        hidden_rows = read_jsonl(args.input_root / "hidden_manifest.jsonl")
        joined, join_errors = join_rows(model_rows, source_rows, target_rows, hidden_rows)
        validation_errors.extend(join_errors)
        schema_rows = schema_leakage_rows(model_rows)
        p_obs_binary, p_obs_labels = p_obs_rows(joined)
        p_rel_binary, p_rel_labels = p_rel_rows(joined)
        probes.extend(shortcut_probes(p_obs_binary, p_obs_labels, "p_obs"))
        probes.extend(shortcut_probes(p_rel_binary, p_rel_labels, "p_rel_observable"))

        if len(model_rows) != EXPECTED_ROWS:
            validation_errors.append({"error_type": "unexpected_model_row_count", "actual": len(model_rows)})
        if Counter(p_obs_labels) != EXPECTED_P_OBS:
            validation_errors.append({"error_type": "unexpected_p_obs_counts", "actual": dict(Counter(p_obs_labels))})
        if Counter(p_rel_labels) != EXPECTED_P_REL:
            validation_errors.append({"error_type": "unexpected_p_rel_counts", "actual": dict(Counter(p_rel_labels))})

    schema_hits = 0
    if schema_rows:
        summary_rows = [row for row in schema_rows if row.get("row_index") == "__summary__"]
        schema_hits = int(summary_rows[0].get("blocked_hits", 0)) if summary_rows else 0
    critical = critical_probe_failures(probes, schema_hits)
    allowed_medium = [
        probe
        for probe in probes
        if probe["allowed_in_model"]
        and probe["risk_level"] == "medium"
        and probe["blocker_policy"] == "block_if_high"
    ]
    hidden_high = [probe for probe in probes if not probe["allowed_in_model"] and probe["risk_level"] == "high"]

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_or_join_errors"
        next_todo = EXPECTED_INPUT_NEXT
        smoke_allowed = False
    elif critical:
        status = STATUS_BLOCKED
        selected_path = "blocked_allowed_model_safe_shortcut_risk"
        next_todo = NEXT_BLOCKED
        smoke_allowed = False
    else:
        status = STATUS_READY
        selected_path = "schema_clean_no_critical_shortcut_smoke_plan_allowed"
        next_todo = NEXT_READY
        smoke_allowed = True

    output_paths = {
        "critical_probe_failures": args.output_dir / "critical_probe_failures.csv",
        "diagnostic_profile": args.output_dir / "diagnostic_profile.csv",
        "p_obs_smoke_ready_view": args.output_dir / "p_obs_smoke_ready_view.jsonl",
        "p_rel_observable_smoke_ready_view": args.output_dir / "p_rel_observable_smoke_ready_view.jsonl",
        "report": args.output_dir / "report.md",
        "schema_leakage": args.output_dir / "schema_leakage.csv",
        "shortcut_probe_summary": args.output_dir / "shortcut_probe_summary.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
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
        },
        "counts": {
            "allowed_high_risk_blockers": len(critical),
            "allowed_medium_risk_probes": len(allowed_medium),
            "hidden_high_risk_probes": len(hidden_high),
            "p_obs_rows": len(p_obs_binary),
            "p_obs_target_counts": dict(Counter(p_obs_labels)),
            "p_rel_rows": len(p_rel_binary),
            "p_rel_target_counts": dict(Counter(p_rel_labels)),
            "rows": len(joined),
            "schema_leakage_hits": schema_hits,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "hidden_manifest": rel_path(args.input_root / "hidden_manifest.jsonl"),
            "model_safe_view": rel_path(args.input_root / "model_safe_view.jsonl"),
            "source_rows": rel_path(args.input_root / "source_rows.jsonl"),
            "summary": rel_path(args.input_root / "summary.json"),
            "target_manifest": rel_path(args.input_root / "target_manifest.jsonl"),
        },
        "learned_smoke_allowed": smoke_allowed,
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_csv(output_paths["schema_leakage"], schema_rows)
    write_csv(output_paths["shortcut_probe_summary"], probes)
    write_csv(output_paths["critical_probe_failures"], critical)
    write_csv(output_paths["diagnostic_profile"], diagnostic_profile(joined))
    write_jsonl(output_paths["p_obs_smoke_ready_view"], smoke_ready_view(p_obs_binary, p_obs_labels, "p_obs"))
    write_jsonl(output_paths["p_rel_observable_smoke_ready_view"], smoke_ready_view(p_rel_binary, p_rel_labels, "p_rel_observable"))
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary, probes, critical), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
