#!/usr/bin/env python3
"""Audit schema leakage and shortcut risk for R6 supported-by decomposition rows."""

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

DEFAULT_INPUT_ROOT = H2_ROOT / "artifacts/route_specific_targets/r6_superordinate_support"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit"

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_v1"
SMOKE_READY_SCHEMA = "h002_r6_supported_by_decomposition_smoke_ready_view_v1"
STATUS_READY = "h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_ready_for_smoke_plan"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_blocked_shortcut_risk"
STATUS_ERROR = "h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_input_errors"
NEXT_READY = "compatibility_dataset_v3_supported_by_decomposition_smoke_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_supported_by_decomposition_path_decision_after_schema_shortcut_audit"

EXPECTED_ROWS = 320
EXPECTED_LABEL_COUNTS = {
    "accept_broad_support": 80,
    "relabel_to_subtype": 80,
    "reject_no_support": 80,
    "abstain": 80,
}
HIGH_RISK_ACC = 0.95
MEDIUM_RISK_ACC = 0.75

ROUTE = {
    "family": "superordinate_support",
    "relation": "supported by",
    "route_id": "R6",
    "route_type": "superordinate_support_decomposition_route",
    "target_axis": "accept_relabel_abstain",
}

REQUIRED_INPUT_FILES = [
    "summary.json",
    "schema.json",
    "model_safe_rows.jsonl",
    "hidden_manifest.jsonl",
    "audit_view.jsonl",
    "control_manifest.json",
    "quota_audit.csv",
    "schema_precheck.csv",
    "selection_profile.csv",
    "validation_errors.jsonl",
]

LABEL_TO_ID = {
    "accept_broad_support": 0,
    "relabel_to_subtype": 1,
    "reject_no_support": 2,
    "abstain": 3,
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
    if not fields:
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
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(flatten_paths(child, next_prefix))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def blocked_fragments(path: str) -> list[str]:
    lower = path.lower()
    fragments = [
        "audit_status",
        "candidate_role",
        "construction",
        "directed_pair",
        "geometry_status",
        "h001",
        "hidden",
        "label_match",
        "machine_hint",
        "matched_",
        "object_id",
        "p_geom",
        "prediction_id",
        "queue_kind",
        "rank_band",
        "reason_code",
        "scan_id",
        "semantic_rank",
        "semantic_score",
        "source_id",
        "subgraph_id",
        "subject_id",
    ]
    return [fragment for fragment in fragments if fragment in lower]


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


def binary_auc(values: list[float], labels: list[int]) -> float | None:
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


def max_one_vs_rest_auc(values: list[float], labels: list[str]) -> tuple[float | None, str]:
    best_auc: float | None = None
    best_label = ""
    for target in sorted(set(labels)):
        binary = [1 if label == target else 0 for label in labels]
        auc = binary_auc(values, binary)
        if auc is not None and (best_auc is None or auc > best_auc):
            best_auc = auc
            best_label = target
    return best_auc, best_label


def categorical_probe(
    rows: list[dict[str, Any]],
    labels: list[str],
    probe_name: str,
    source: str,
    allowed_feature: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
    target_scope: str,
) -> dict[str, Any]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
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
        "target_scope": target_scope,
    }


def numeric_probe(
    rows: list[dict[str, Any]],
    labels: list[str],
    probe_name: str,
    source: str,
    allowed_feature: bool,
    value_fn: Callable[[dict[str, Any]], Any],
    interpretation: str,
    target_scope: str,
) -> dict[str, Any]:
    pairs: list[tuple[float, str]] = []
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
            "probe_type": "numeric_threshold_multiclass",
            "risk_level": "low",
            "rows": len(rows),
            "source": source,
            "target_scope": target_scope,
        }

    all_labels = sorted(set(labels))
    values = sorted({value for value, _ in pairs})
    thresholds = values if len(values) == 1 else [(left + right) / 2.0 for left, right in zip(values, values[1:])]
    if len(thresholds) > 3000:
        step = max(1, len(thresholds) // 3000)
        thresholds = thresholds[::step]
    fallback = Counter(labels).most_common(1)[0][0]
    best_accuracy = -1.0
    best_rule = ""
    for threshold in thresholds:
        for direction in ("ge", "lt"):
            left_counts: Counter[str] = Counter()
            right_counts: Counter[str] = Counter()
            for value, label in pairs:
                if value >= threshold if direction == "ge" else value < threshold:
                    right_counts[label] += 1
                else:
                    left_counts[label] += 1
            left_label = left_counts.most_common(1)[0][0] if left_counts else fallback
            right_label = right_counts.most_common(1)[0][0] if right_counts else fallback
            correct = 0
            for row, label in zip(rows, labels):
                value = safe_float(value_fn(row))
                if value is None:
                    pred = fallback
                elif value >= threshold if direction == "ge" else value < threshold:
                    pred = right_label
                else:
                    pred = left_label
                correct += int(pred == label)
            accuracy = correct / len(labels) if labels else 0.0
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_rule = f"{direction}_{threshold:.8g}_left={left_label}_right={right_label}"
    auc, auc_label = max_one_vs_rest_auc([value for value, _ in pairs], [label for _, label in pairs])
    return {
        "accuracy": round(best_accuracy, 6),
        "allowed_feature": allowed_feature,
        "auroc": round(auc, 6) if auc is not None else "",
        "best_one_vs_rest_label": auc_label,
        "best_rule": best_rule,
        "interpretation": interpretation,
        "missing": missing,
        "num_labels": len(all_labels),
        "num_values": len(values),
        "probe_name": probe_name,
        "probe_type": "numeric_threshold_multiclass",
        "risk_level": risk_level(best_accuracy, auc),
        "rows": len(rows),
        "source": source,
        "target_scope": target_scope,
    }


def validate_inputs(summary: dict[str, Any], schema: dict[str, Any], input_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for name in REQUIRED_INPUT_FILES:
        if not (input_root / name).exists():
            errors.append({"error_type": "missing_input_file", "path": rel_path(input_root / name)})
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors_present", "actual": summary.get("validation_errors")})
    if (input_root / "validation_errors.jsonl").exists() and (input_root / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_input_validation_errors"})
    for key, expected in ROUTE.items():
        if summary.get("route", {}).get(key) != expected:
            errors.append({"error_type": "route_summary_mismatch", "field": key, "actual": summary.get("route", {}).get(key), "expected": expected})
        if schema.get("route", {}).get(key) != expected:
            errors.append({"error_type": "route_schema_mismatch", "field": key, "actual": schema.get("route", {}).get(key), "expected": expected})
    counts = summary.get("counts", {})
    if counts.get("total_rows") != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_total_rows", "actual": counts.get("total_rows"), "expected": EXPECTED_ROWS})
    if counts.get("decomposition_label_counts") != EXPECTED_LABEL_COUNTS:
        errors.append({"error_type": "unexpected_label_counts", "actual": counts.get("decomposition_label_counts"), "expected": EXPECTED_LABEL_COUNTS})
    boundary = summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "paper_evidence_allowed", "runs_learned_smoke", "test_usage", "trains_new_model", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def join_rows(
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    hidden_by_id = {row["row_id"]: row for row in hidden_rows if "row_id" in row}
    audit_by_id = {row["row_id"]: row for row in audit_rows if "row_id" in row}
    joined: list[dict[str, Any]] = []
    for model in model_rows:
        row_id = model.get("row_id")
        hidden = hidden_by_id.get(row_id)
        audit = audit_by_id.get(row_id)
        if hidden is None or audit is None:
            errors.append({"error_type": "missing_join_row", "row_id": row_id, "has_hidden": hidden is not None, "has_audit": audit is not None})
            continue
        joined.append({"audit": audit, "hidden": hidden, "model": model})
    for name, rows, row_map in [("hidden", hidden_rows, hidden_by_id), ("audit", audit_rows, audit_by_id)]:
        if len(rows) != len(row_map):
            errors.append({"error_type": f"duplicate_{name}_row_ids", "rows": len(rows), "unique": len(row_map)})
    return joined, errors


def labels_for(joined: list[dict[str, Any]]) -> list[str]:
    return [str(nested_get(row["model"], "labels.supported_by_decomposition_label")) for row in joined]


def observable_subset(joined: list[dict[str, Any]], labels: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    out_labels: list[str] = []
    for row, label in zip(joined, labels):
        if label != "abstain":
            rows.append(row)
            out_labels.append(label)
    return rows, out_labels


def feature_path_audit(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: Counter[str] = Counter()
    hit_rows: Counter[str] = Counter()
    for row in model_rows:
        row_hits: set[str] = set()
        for path in flatten_paths(row.get("feature_blocks", {}), "feature_blocks"):
            fragments = blocked_fragments(path)
            if fragments:
                key = f"{path}::{','.join(fragments)}"
                hits[key] += 1
                row_hits.add(key)
        for key in row_hits:
            hit_rows[key] += 1
    if not hits:
        return [{"feature_path": "__summary__", "blocked_fragments": "", "hits": 0, "rows": len(model_rows), "passed": True}]
    rows = []
    for key, count in sorted(hits.items()):
        path, fragments = key.split("::", 1)
        rows.append({"feature_path": path, "blocked_fragments": fragments, "hits": count, "rows": hit_rows[key], "passed": False})
    rows.append({"feature_path": "__summary__", "blocked_fragments": "", "hits": sum(hits.values()), "rows": len(model_rows), "passed": False})
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


def make_probes(rows: list[dict[str, Any]], labels: list[str], target_scope: str) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    get_m = lambda dotted: (lambda row: nested_get(row["model"], dotted))
    get_h = lambda dotted: (lambda row: nested_get(row["hidden"], dotted))
    get_a = lambda dotted: (lambda row: nested_get(row["audit"], dotted))

    probes.extend(
        [
            categorical_probe(rows, labels, "model_T_predicate_label", "model_safe_T_e", True, get_m("feature_blocks.T_e.predicate_label"), "predicate is constant but checked", target_scope),
            categorical_probe(rows, labels, "model_T_subject_class", "model_safe_T_e", True, get_m("feature_blocks.T_e.subject_class_text"), "subject-class shortcut check", target_scope),
            categorical_probe(rows, labels, "model_T_object_class", "model_safe_T_e", True, get_m("feature_blocks.T_e.object_class_text"), "object-class shortcut check", target_scope),
            categorical_probe(
                rows,
                labels,
                "model_T_subject_object_class_pair",
                "model_safe_T_e",
                True,
                lambda row: f"{nested_get(row['model'], 'feature_blocks.T_e.subject_class_text')}->{nested_get(row['model'], 'feature_blocks.T_e.object_class_text')}",
                "class-pair shortcut check",
                target_scope,
            ),
            categorical_probe(rows, labels, "model_Q_observability_status", "model_safe_Q_e", True, get_m("feature_blocks.Q_e.observability_status"), "Q_e should mainly separate abstain, not copy all classes", target_scope),
            categorical_probe(rows, labels, "model_Q_generic_endpoint_visible", "model_safe_Q_e", True, get_m("feature_blocks.Q_e.generic_endpoint_visible"), "generic endpoint shortcut check", target_scope),
            categorical_probe(rows, labels, "model_Q_geometry_contradiction", "model_safe_Q_e", True, get_m("feature_blocks.Q_e.geometry_contradiction"), "geometry contradiction shortcut check", target_scope),
            categorical_probe(rows, labels, "hidden_label_match_status", "hidden_construction", False, get_h("label_match_status"), "GT/pair-match construction status if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_candidate_role", "hidden_construction", False, get_h("candidate_role"), "candidate role mirrors construction if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_machine_hint", "hidden_construction", False, get_h("machine_hint"), "machine hint if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_matched_predicates", "hidden_gt_match", False, get_h("matched_predicates"), "matched GT predicates if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_subtype_relabel_target", "hidden_target_detail", False, get_h("subtype_relabel_target"), "subtype target if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_evidence_reason", "hidden_construction", False, get_h("evidence_reason"), "human-readable construction reason if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_queue_kind", "hidden_source_confidence", False, get_h("queue_kind"), "HL/LH source bucket if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_rank_band", "hidden_source_confidence", False, get_h("rank_band"), "rank-band shortcut if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_hard_surface_pair", "hidden_endpoint_type", False, get_h("hard_surface_pair"), "hard-surface slice risk", target_scope),
            categorical_probe(rows, labels, "hidden_generic_endpoint_visible", "hidden_endpoint_type", False, get_h("generic_endpoint_visible"), "generic endpoint if leaked", target_scope),
            categorical_probe(rows, labels, "hidden_scan_id", "hidden_identity", False, get_h("scan_id"), "scan memorization if leaked", target_scope),
            categorical_probe(rows, labels, "audit_evidence_reason", "audit_visible_for_review_only", False, get_a("evidence_reason"), "audit-view reason is not model input", target_scope),
        ]
    )

    sample_model_rows = [row["model"] for row in rows]
    for field in numeric_feature_paths(sample_model_rows, "G_e_mesh_pose_contact"):
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"model_G_e_{field}",
                "model_safe_G_e",
                True,
                get_m(f"feature_blocks.G_e_mesh_pose_contact.{field}"),
                "single geometry feature threshold check",
                target_scope,
            )
        )
    for field in ["semantic_score_norm", "semantic_score_raw", "semantic_rank", "p_geom_valid"]:
        probes.append(
            numeric_probe(
                rows,
                labels,
                f"hidden_{field}",
                "hidden_source_or_geometry_score",
                False,
                get_h(field),
                "hidden source score/rank/H001 geometry score if leaked",
                target_scope,
            )
        )
    return probes


def label_profile(joined: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    axes: list[tuple[str, Callable[[dict[str, Any]], Any]]] = [
        ("target_label", lambda row: nested_get(row["model"], "labels.supported_by_decomposition_label")),
        ("p_obs", lambda row: nested_get(row["model"], "labels.p_obs")),
        ("p_rel", lambda row: nested_get(row["model"], "labels.p_rel")),
        ("subtype_relabel_target", lambda row: nested_get(row["model"], "labels.subtype_relabel_target")),
        ("class_pair", lambda row: nested_get(row["hidden"], "class_pair")),
        ("label_match_status", lambda row: nested_get(row["hidden"], "label_match_status")),
        ("matched_predicates", lambda row: nested_get(row["hidden"], "matched_predicates")),
        ("rank_band", lambda row: nested_get(row["hidden"], "rank_band")),
        ("queue_kind", lambda row: nested_get(row["hidden"], "queue_kind")),
        ("hard_surface_pair", lambda row: nested_get(row["hidden"], "hard_surface_pair")),
        ("generic_endpoint_visible", lambda row: nested_get(row["hidden"], "generic_endpoint_visible")),
    ]
    out: list[dict[str, Any]] = []
    for axis, fn in axes:
        by_value: dict[str, Counter[str]] = defaultdict(Counter)
        for row, label in zip(joined, labels):
            by_value[value_key(fn(row))][label] += 1
        for value, counts in sorted(by_value.items()):
            out.append({"axis": axis, "value": value, "rows": sum(counts.values()), **{f"label_{label}": counts.get(label, 0) for label in EXPECTED_LABEL_COUNTS}})
    return out


def route_specific_checks(joined: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    label_counts = Counter(labels)
    class_pair_label_counts: dict[str, Counter[str]] = defaultdict(Counter)
    no_gt_counts: Counter[str] = Counter()
    pair_other_counts: Counter[str] = Counter()
    generic_abstain = 0
    hard_surface_rows = 0
    for row, label in zip(joined, labels):
        hidden = row["hidden"]
        class_pair_label_counts[str(hidden.get("class_pair"))][label] += 1
        if hidden.get("label_match_status") == "no_gt_for_pair":
            no_gt_counts[label] += 1
        if hidden.get("label_match_status") == "pair_has_other_predicate":
            pair_other_counts[label] += 1
        if label == "abstain" and hidden.get("generic_endpoint_visible"):
            generic_abstain += 1
        if hidden.get("hard_surface_pair"):
            hard_surface_rows += 1
    mixed_cells = sum(1 for counts in class_pair_label_counts.values() if sum(1 for count in counts.values() if count > 0) >= 2)
    max_class_pair_acc = 0.0
    if joined:
        max_class_pair_acc = sum(max(counts.values()) for counts in class_pair_label_counts.values()) / len(joined)
    return [
        {"check": "row_count", "observed": len(joined), "expected": EXPECTED_ROWS, "passed": len(joined) == EXPECTED_ROWS},
        {"check": "label_balance", "observed": json.dumps(dict(sorted(label_counts.items())), sort_keys=True), "expected": json.dumps(EXPECTED_LABEL_COUNTS, sort_keys=True), "passed": dict(sorted(label_counts.items())) == EXPECTED_LABEL_COUNTS},
        {"check": "mixed_class_pair_cells", "observed": mixed_cells, "expected_min": 12, "passed": mixed_cells >= 12},
        {"check": "class_pair_majority_accuracy", "observed": round(max_class_pair_acc, 6), "risk_threshold": MEDIUM_RISK_ACC, "passed": max_class_pair_acc < HIGH_RISK_ACC},
        {"check": "no_gt_not_used_as_negative_only", "observed": json.dumps(dict(sorted(no_gt_counts.items())), sort_keys=True), "passed": no_gt_counts.get("reject_no_support", 0) == 0},
        {"check": "pair_has_other_predicate_not_all_reject", "observed": json.dumps(dict(sorted(pair_other_counts.items())), sort_keys=True), "passed": len(pair_other_counts) >= 2},
        {"check": "generic_endpoint_abstain_rows", "observed": generic_abstain, "expected_max": 40, "passed": generic_abstain <= 40},
        {"check": "hard_surface_rows", "observed": hard_surface_rows, "expected_max": 176, "passed": hard_surface_rows <= 176},
    ]


def smoke_ready_view(joined: list[dict[str, Any]], labels: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row, label in zip(joined, labels):
        scan_id = str(row["hidden"].get("scan_id", "missing"))
        group_hash = hashlib.sha1(scan_id.encode("utf-8")).hexdigest()[:12]
        rows.append(
            {
                "feature_blocks": row["model"]["feature_blocks"],
                "row_id": row["model"]["row_id"],
                "schema_version": SMOKE_READY_SCHEMA,
                "split": "train",
                "split_metadata": {
                    "cv_group_id": f"scan_{group_hash}",
                    "group_use": "split_only_not_model_feature",
                },
                "target_label": label,
                "target_label_id": LABEL_TO_ID[label],
                "target_task": "supported_by_decomposition_4way",
            }
        )
    return rows


def build_report(summary: dict[str, Any], probes: list[dict[str, Any]]) -> str:
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
    )[:10]
    lines = [
        "# H002 R6 Supported-By Decomposition Schema Shortcut Audit",
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
        f"- rows: `{counts['rows']}`",
        f"- labels: `{counts['label_counts']}`",
        f"- observable rows: `{counts['observable_rows']}`",
        f"- schema leakage hits: `{counts['schema_leakage_hits']}`",
        f"- allowed high-risk probes: `{counts['allowed_high_risk_probes']}`",
        f"- allowed medium-risk probes: `{counts['allowed_medium_risk_probes']}`",
        f"- hidden high-risk probes: `{counts['hidden_high_risk_probes']}`",
        "",
        "## Interpretation",
        "",
        "- `model_safe_rows` are checked separately from hidden construction fields.",
        "- `T_e`, `G_e_mesh_pose_contact`, and `Q_e` are allowed model-safe blocks.",
        "- Hidden `label_match_status`, `machine_hint`, `matched_predicates`, source rank/score, scan identity, and audit reasons are reported only as leakage risks.",
        "- This step does not run learned smoke, does not train a model, and does not use validation/test data.",
    ]
    if summary["status"] == STATUS_READY:
        lines.append("- No high-risk allowed model-safe probe or schema leakage was found; smoke planning is allowed.")
    elif summary["status"] == STATUS_BLOCKED:
        lines.append("- At least one allowed model-safe probe is high-risk; learned smoke remains blocked pending path decision.")
    lines.extend(["", "## Top Allowed Probes", ""])
    for probe in top_allowed:
        lines.append(
            f"- `{probe['probe_name']}` / `{probe['target_scope']}`: acc `{probe['accuracy']}`, auroc `{probe.get('auroc', '')}`, risk `{probe['risk_level']}`, source `{probe['source']}`"
        )
    lines.extend(["", "## Top Hidden/Control Probes", ""])
    for probe in top_hidden:
        lines.append(
            f"- `{probe['probe_name']}` / `{probe['target_scope']}`: acc `{probe['accuracy']}`, auroc `{probe.get('auroc', '')}`, risk `{probe['risk_level']}`, source `{probe['source']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_summary = read_json(args.input_root / "summary.json")
    input_schema = read_json(args.input_root / "schema.json")
    validation_errors = validate_inputs(input_summary, input_schema, args.input_root)

    model_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    joined: list[dict[str, Any]] = []
    labels: list[str] = []
    probes: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    profile_rows: list[dict[str, Any]] = []
    route_checks: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []

    if not validation_errors:
        model_rows = read_jsonl(args.input_root / "model_safe_rows.jsonl")
        hidden_rows = read_jsonl(args.input_root / "hidden_manifest.jsonl")
        audit_rows = read_jsonl(args.input_root / "audit_view.jsonl")
        joined, join_errors = join_rows(model_rows, hidden_rows, audit_rows)
        validation_errors.extend(join_errors)
        feature_rows = feature_path_audit(model_rows)
        labels = labels_for(joined)
        label_counts = Counter(labels)
        if dict(sorted(label_counts.items())) != EXPECTED_LABEL_COUNTS:
            validation_errors.append({"error_type": "joined_label_count_mismatch", "actual": dict(sorted(label_counts.items())), "expected": EXPECTED_LABEL_COUNTS})
        if len(joined) != EXPECTED_ROWS:
            validation_errors.append({"error_type": "joined_row_count_mismatch", "actual": len(joined), "expected": EXPECTED_ROWS})
        probes = make_probes(joined, labels, "4way_all")
        obs_rows, obs_labels = observable_subset(joined, labels)
        probes.extend(make_probes(obs_rows, obs_labels, "3way_observable_only"))
        profile_rows = label_profile(joined, labels)
        route_checks = route_specific_checks(joined, labels)
        smoke_rows = smoke_ready_view(joined, labels)

    schema_leakage_hits = 0
    for row in feature_rows:
        if row.get("feature_path") == "__summary__":
            schema_leakage_hits = int(row.get("hits", 0))
            break
    allowed_high = [probe for probe in probes if probe["allowed_feature"] and probe["risk_level"] == "high"]
    allowed_medium = [probe for probe in probes if probe["allowed_feature"] and probe["risk_level"] == "medium"]
    hidden_high = [probe for probe in probes if not probe["allowed_feature"] and probe["risk_level"] == "high"]
    critical_rows = allowed_high + (
        [{"probe_name": "schema_feature_path_leakage", "risk_level": "high", "accuracy": 1.0, "allowed_feature": True}]
        if schema_leakage_hits
        else []
    )
    for row in route_checks:
        if row.get("passed") is False and row.get("check") in {"row_count", "label_balance", "no_gt_not_used_as_negative_only"}:
            critical_rows.append({"probe_name": row.get("check"), "risk_level": "high", "accuracy": 1.0, "allowed_feature": True, "detail": row.get("observed")})

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_or_join_errors"
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
        },
        "counts": {
            "allowed_high_risk_probes": len(allowed_high),
            "allowed_medium_risk_probes": len(allowed_medium),
            "hidden_high_risk_probes": len(hidden_high),
            "label_counts": dict(sorted(Counter(labels).items())),
            "observable_rows": sum(1 for label in labels if label != "abstain"),
            "rows": len(joined),
            "schema_leakage_hits": schema_leakage_hits,
            "smoke_ready_rows": len(smoke_rows),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "audit_view": rel_path(args.input_root / "audit_view.jsonl"),
            "hidden_manifest": rel_path(args.input_root / "hidden_manifest.jsonl"),
            "model_safe_rows": rel_path(args.input_root / "model_safe_rows.jsonl"),
            "summary": rel_path(args.input_root / "summary.json"),
        },
        "next_todo": next_todo,
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "critical_probe_failures": rel_path(args.output_dir / "critical_probe_failures.csv"),
            "feature_path_audit": rel_path(args.output_dir / "feature_path_audit.csv"),
            "label_profile": rel_path(args.output_dir / "label_profile.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "route_specific_checks": rel_path(args.output_dir / "route_specific_checks.csv"),
            "shortcut_probe_summary": rel_path(args.output_dir / "shortcut_probe_summary.csv"),
            "smoke_ready_view": rel_path(args.output_dir / "smoke_ready_view.jsonl"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "route": ROUTE,
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_csv(args.output_dir / "feature_path_audit.csv", feature_rows)
    write_csv(args.output_dir / "shortcut_probe_summary.csv", probes)
    write_csv(args.output_dir / "critical_probe_failures.csv", critical_rows)
    write_csv(args.output_dir / "label_profile.csv", profile_rows)
    write_csv(args.output_dir / "route_specific_checks.csv", route_checks)
    write_jsonl(args.output_dir / "smoke_ready_view.jsonl", smoke_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(build_report(summary, probes), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
