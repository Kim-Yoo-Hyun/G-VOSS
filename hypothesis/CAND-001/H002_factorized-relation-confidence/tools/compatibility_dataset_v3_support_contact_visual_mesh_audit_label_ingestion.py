#!/usr/bin/env python3
"""Ingest support/contact audit labels after visible-packet label lock."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_FILL_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill"
)
DEFAULT_PACKET_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion"
)

EXPECTED_FILL_STATUS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_completed"
EXPECTED_FILL_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion"
EXPECTED_PACKET_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_ready_for_label_fill"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion_v1"
TARGET_SCHEMA_VERSION = "h002_support_contact_visual_mesh_audit_targets_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_ready_for_path_decision"
)
STATUS_SHORTCUT_RISK = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_shortcut_risk_blocks_smoke"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion_errors"
SELECTED_PATH = "ingest_proxy_labels_run_independence_diagnostics_block_smoke_if_shortcut"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion"

TARGET_ROWS = 480
MIN_BINARY_CLASS = 80
MIN_DIAGNOSTIC_CLASS = 30
RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}

REL_MAP = {"accept": 1, "reject": 0}
GEOM_MAP = {"supports": 1, "contradicts": 0}
OBS_MAP = {"sufficient": 1, "limited": 1, "not_evaluable": 0}
Q_ORDINAL = {"not_evaluable": 0, "limited": 1, "sufficient": 2}

PREDICTOR_CATEGORIES = {
    "visible_semantic": {
        "predicate_label",
        "subject_label",
        "object_label",
        "subject_object_class_pair",
        "hard_surface_pair_visible_proxy",
    },
    "label_derived": {
        "review_geometry_support",
        "review_observability",
        "review_counter_relation",
        "review_uncertainty_reason",
        "decision_reason",
    },
    "construction_or_source_hidden": {
        "construction_bucket_hidden",
        "hidden_stratum_hidden",
        "queue_kind_hidden",
        "geometry_status_hidden",
        "label_match_status_hidden",
        "rank_band_hidden",
        "source_rank_band_hidden",
        "p_geom_valid_bin_hidden",
        "h001_verification_status_hidden",
        "machine_hint_hidden",
        "hard_surface_pair_hidden",
    },
    "instance_or_scan_id": {
        "scan_id_hidden",
        "subgraph_id_hidden",
        "directed_pair_key_hidden",
    },
}

RISK_PREDICTORS = sorted({field for fields in PREDICTOR_CATEGORIES.values() for field in fields})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-dir", type=Path, default=DEFAULT_FILL_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fields.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def rank_band(value: Any) -> str:
    try:
        rank = float(value)
    except (TypeError, ValueError):
        return "rank_missing"
    if rank <= 50:
        return "rank_1_50"
    if rank <= 100:
        return "rank_51_100"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def p_geom_bin(value: Any) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "missing"
    if score >= 0.90:
        return "p_geom_ge_0_90"
    if score >= 0.70:
        return "p_geom_0_70_0_90"
    if score >= 0.50:
        return "p_geom_0_50_0_70"
    if score >= 0.30:
        return "p_geom_0_30_0_50"
    return "p_geom_lt_0_30"


def validate_inputs(
    fill_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    filled_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fill_summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "actual": fill_summary.get("status")})
    if fill_summary.get("next_todo") != EXPECTED_FILL_NEXT:
        errors.append({"error_type": "unexpected_fill_next_todo", "actual": fill_summary.get("next_todo")})
    if fill_summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": fill_summary.get("validation_errors")})
    if packet_summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"error_type": "unexpected_packet_status", "actual": packet_summary.get("status")})
    if packet_summary.get("validation_errors") != 0:
        errors.append({"error_type": "packet_validation_errors_present", "actual": packet_summary.get("validation_errors")})
    if len(filled_rows) != TARGET_ROWS:
        errors.append({"error_type": "filled_row_count_mismatch", "actual": len(filled_rows), "expected": TARGET_ROWS})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "hidden_row_count_mismatch", "actual": len(hidden_rows), "expected": TARGET_ROWS})
    filled_ids = {row["review_id"] for row in filled_rows}
    hidden_ids = {row["review_id"] for row in hidden_rows}
    if filled_ids != hidden_ids:
        errors.append({"error_type": "review_id_set_mismatch"})
    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_learned_smoke",
        "trains_new_model",
        "used_hidden_manifest",
        "used_source_score_or_rank",
        "used_old_geometry_status_or_p_geom_valid",
        "used_label_match_status",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def derive_targets(filled: dict[str, Any], hidden: dict[str, Any]) -> dict[str, Any]:
    relation_label = filled["review_relation_reliability"]
    geometry_label = filled["review_geometry_support"]
    observability = filled["review_observability"]
    p_rel_target = REL_MAP.get(relation_label)
    c_e_target = GEOM_MAP.get(geometry_label)
    p_obs_target = OBS_MAP.get(observability)
    q_e_target = Q_ORDINAL.get(observability)
    return {
        "schema_version": TARGET_SCHEMA_VERSION,
        "review_id": filled["review_id"],
        "subject_label": filled["subject_label"],
        "predicate_label": filled["predicate_label"],
        "object_label": filled["object_label"],
        "subject_object_class_pair": f"{filled['subject_label']}->{filled['object_label']}",
        "review_relation_reliability": relation_label,
        "review_geometry_support": geometry_label,
        "review_observability": observability,
        "review_counter_relation": filled["review_counter_relation"],
        "review_uncertainty_reason": filled["review_uncertainty_reason"],
        "decision_reason": filled["decision_reason"],
        "label_provenance": filled["reviewer_id"],
        "user_requested_codex_fill": True,
        "p_rel_target": p_rel_target,
        "p_rel_usable": p_rel_target is not None,
        "c_e_compatibility_target": c_e_target,
        "c_e_usable": c_e_target is not None,
        "p_obs_target": p_obs_target,
        "q_e_observability_ordinal": q_e_target,
        "relation_multiclass_target": relation_label,
        "geometry_support_multiclass_target": geometry_label,
        "hidden_join_after_label_lock": True,
        "hidden_fields_used_for_label_fill": False,
        "source_score_or_rank_used_for_label_fill": False,
        "old_geometry_used_for_label_fill": False,
        "scan_id_hidden": hidden.get("scan_id"),
        "subgraph_id_hidden": hidden.get("subgraph_id"),
        "directed_pair_key_hidden": hidden.get("directed_pair_key"),
        "construction_bucket_hidden": hidden.get("construction_bucket"),
        "hidden_stratum_hidden": hidden.get("hidden_stratum"),
        "queue_kind_hidden": hidden.get("queue_kind"),
        "geometry_status_hidden": hidden.get("geometry_status"),
        "label_match_status_hidden": hidden.get("label_match_status"),
        "rank_band_hidden": hidden.get("rank_band"),
        "source_rank_hidden": hidden.get("source_rank"),
        "source_rank_band_hidden": rank_band(hidden.get("source_rank")),
        "source_score_hidden": hidden.get("source_score"),
        "source_score_raw_hidden": hidden.get("source_score_raw"),
        "p_geom_valid_hidden": hidden.get("p_geom_valid"),
        "p_geom_valid_bin_hidden": p_geom_bin(hidden.get("p_geom_valid")),
        "h001_verification_status_hidden": hidden.get("h001_verification_status"),
        "machine_hint_hidden": hidden.get("machine_hint"),
        "hard_surface_pair_hidden": str(hidden.get("hard_surface_pair")),
        "hard_surface_pair_visible_proxy": str(hidden.get("hard_surface_pair")),
        "packet_status_hidden": hidden.get("packet_status_hidden"),
        "subject_image_count_hidden": hidden.get("subject_image_count_hidden"),
        "object_image_count_hidden": hidden.get("object_image_count_hidden"),
    }


def entropy(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    out = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            out -= p * math.log2(p)
    return out


def normalized_mutual_information(rows: list[dict[str, Any]], predictor: str, target: str) -> float:
    x_counts = Counter(str(row.get(predictor)) for row in rows)
    y_counts = Counter(str(row.get(target)) for row in rows)
    joint = Counter((str(row.get(predictor)), str(row.get(target))) for row in rows)
    n = len(rows)
    if n == 0:
        return 0.0
    mi = 0.0
    for (x, y), count in joint.items():
        pxy = count / n
        px = x_counts[x] / n
        py = y_counts[y] / n
        if pxy > 0 and px > 0 and py > 0:
            mi += pxy * math.log2(pxy / (px * py))
    hx = entropy(x_counts)
    hy = entropy(y_counts)
    if hx <= 0 or hy <= 0:
        return 0.0
    return mi / math.sqrt(hx * hy)


def predictor_category(predictor: str) -> str:
    for category, fields in PREDICTOR_CATEGORIES.items():
        if predictor in fields:
            return category
    return "other"


def shortcut_rows(rows: list[dict[str, Any]], target: str, target_name: str) -> list[dict[str, Any]]:
    usable = [row for row in rows if row.get(target) is not None]
    if not usable:
        return []
    target_counts = Counter(str(row.get(target)) for row in usable)
    baseline_acc = max(target_counts.values()) / len(usable)
    diagnostics: list[dict[str, Any]] = []
    for predictor in RISK_PREDICTORS:
        groups: dict[str, list[str]] = defaultdict(list)
        for row in usable:
            groups[str(row.get(predictor))].append(str(row.get(target)))
        correct = 0
        mixed_groups = 0
        large_pure_groups = 0
        max_group_rows = 0
        for labels in groups.values():
            counts = Counter(labels)
            correct += max(counts.values())
            max_group_rows = max(max_group_rows, len(labels))
            if len(counts) > 1:
                mixed_groups += 1
            purity = max(counts.values()) / len(labels)
            if len(labels) >= RISK_THRESHOLDS["large_group_rows"] and purity >= RISK_THRESHOLDS["large_group_purity"]:
                large_pure_groups += 1
        majority_acc = correct / len(usable)
        nmi = normalized_mutual_information(usable, predictor, target)
        excess = majority_acc - baseline_acc
        category = predictor_category(predictor)
        threshold_hit = (
            majority_acc >= RISK_THRESHOLDS["majority_rule_accuracy"]
            or excess >= RISK_THRESHOLDS["majority_excess_over_baseline"]
            or nmi >= RISK_THRESHOLDS["normalized_mutual_information"]
            or large_pure_groups > 0
        )
        if category == "label_derived" and threshold_hit:
            risk = "blocked_if_used_label_derived"
        elif threshold_hit:
            risk = "high"
        else:
            risk = "low"
        diagnostics.append(
            {
                "target_name": target_name,
                "target_field": target,
                "predictor": predictor,
                "predictor_category": category,
                "rows": len(usable),
                "target_counts": dict(target_counts),
                "baseline_accuracy": baseline_acc,
                "majority_rule_accuracy": majority_acc,
                "majority_excess_over_baseline": excess,
                "normalized_mutual_information": nmi,
                "num_groups": len(groups),
                "mixed_groups": mixed_groups,
                "max_group_rows": max_group_rows,
                "large_pure_groups": large_pure_groups,
                "risk": risk,
            }
        )
    return diagnostics


def target_viability_rows(rows: list[dict[str, Any]], shortcut: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("p_rel_binary", "p_rel_target", "relation reliability accept vs reject, abstain excluded", MIN_BINARY_CLASS),
        ("c_e_compatibility_binary", "c_e_compatibility_target", "geometry support vs contradiction, ambiguous excluded", MIN_BINARY_CLASS),
        ("p_obs_binary", "p_obs_target", "evidence sufficient/limited vs not evaluable", MIN_DIAGNOSTIC_CLASS),
        ("q_e_observability_ordinal", "q_e_observability_ordinal", "observability ordinal", MIN_DIAGNOSTIC_CLASS),
        ("relation_multiclass", "relation_multiclass_target", "accept/reject/abstain diagnostic", MIN_DIAGNOSTIC_CLASS),
    ]
    shortcut_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in shortcut:
        shortcut_by_target[row["target_name"]].append(row)
    out: list[dict[str, Any]] = []
    for name, field, role, min_class in specs:
        usable = [row for row in rows if row.get(field) is not None]
        counts = Counter(str(row.get(field)) for row in usable)
        min_count = min(counts.values()) if counts else 0
        class_mass_pass = len(counts) >= 2 and min_count >= min_class
        high_risk_predictors = [
            row["predictor"]
            for row in shortcut_by_target.get(name, [])
            if row["risk"] == "high" and row["predictor_category"] != "label_derived"
        ]
        smoke_allowed = class_mass_pass and not high_risk_predictors and name in {"p_rel_binary", "c_e_compatibility_binary"}
        out.append(
            {
                "target_name": name,
                "target_field": field,
                "role": role,
                "rows": len(usable),
                "class_counts": dict(counts),
                "num_classes": len(counts),
                "min_class_count": min_count,
                "min_class_threshold": min_class,
                "class_mass_pass": class_mass_pass,
                "high_risk_predictors": ";".join(high_risk_predictors[:12]),
                "high_risk_predictor_count": len(high_risk_predictors),
                "learned_smoke_allowed": smoke_allowed,
            }
        )
    return out


def target_count_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "predicate_label",
        "review_relation_reliability",
        "review_geometry_support",
        "review_observability",
        "review_counter_relation",
        "review_uncertainty_reason",
        "p_rel_target",
        "c_e_compatibility_target",
        "p_obs_target",
        "q_e_observability_ordinal",
        "construction_bucket_hidden",
        "queue_kind_hidden",
        "geometry_status_hidden",
        "label_match_status_hidden",
    ]
    out: list[dict[str, Any]] = []
    for field in fields:
        counts = Counter(str(row.get(field)) for row in rows)
        total = sum(counts.values()) or 1
        for value, count in counts.most_common():
            out.append({"axis": field, "value": value, "count": count, "share": count / total})
    combo = Counter((row["predicate_label"], row["review_relation_reliability"]) for row in rows)
    for (predicate, label), count in sorted(combo.items()):
        pred_total = sum(1 for row in rows if row["predicate_label"] == predicate) or 1
        out.append({"axis": "predicate_x_reliability", "value": f"{predicate}|{label}", "count": count, "share": count / pred_total})
    return out


def risk_register_rows(viability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "risk": "codex_proxy_label_not_independent_human_audit",
            "severity": "high",
            "evidence": "label provenance is codex_visible_packet_proxy_labeler_user_requested",
            "action": "do not present as independent blind human audit; use for target plumbing and diagnostics only",
        },
        {
            "risk": "visible_class_pair_shortcut",
            "severity": "high",
            "evidence": "subject_object_class_pair nearly predicts p_rel/C_e in current proxy labels",
            "action": "block learned smoke until repair or class-pair controlled evaluation is designed",
        },
        {
            "risk": "construction_proxy_shortcut",
            "severity": "high",
            "evidence": "construction_bucket/hidden_stratum/label_match_status are highly predictive after hidden join",
            "action": "keep construction fields out of model views; use only for audit and balancing",
        },
        {
            "risk": "p_obs_degenerate",
            "severity": "medium",
            "evidence": "all 480 rows have sufficient observability after packet materialization",
            "action": "do not claim p_obs learning from this fill; mine limited/not-evaluable rows separately if p_obs is needed",
        },
        {
            "risk": "mesh_card_not_full_contact_render",
            "severity": "medium",
            "evidence": "mesh_contact_render is an availability card rather than full contact-surface visualization",
            "action": "treat mesh evidence as audit context; full mesh-contact render requires separate asset hardening",
        },
        {
            "risk": "learned_smoke_premature",
            "severity": "high",
            "evidence": "; ".join(
                f"{row['target_name']} smoke_allowed={row['learned_smoke_allowed']}" for row in viability
            ),
            "action": "run path decision and target repair before any model training",
        },
    ]


def target_jsonl(rows: list[dict[str, Any]], field: str, usable_field: str | None = None) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row.get(field) is None:
            continue
        if usable_field is not None and not row.get(usable_field):
            continue
        out.append(
            {
                "review_id": row["review_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "target": row[field],
                "target_field": field,
                "label_provenance": row["label_provenance"],
            }
        )
    return out


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Label Ingestion",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Target Summary",
            "",
            "```json",
            json.dumps(summary["target_summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            "Learned smoke remains blocked. The binary class mass is sufficient, but the current proxy labels are highly predictable from visible class-pair and hidden construction/source fields. This artifact is useful for target plumbing and diagnosis, not for paper-level reliability claims.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(args.fill_dir / "summary.json")
    packet_summary = read_json(args.packet_dir / "summary.json")
    filled_rows = read_csv(args.fill_dir / "filled_visible_review_sheet.csv")
    hidden_rows = read_jsonl(args.packet_dir / "materialized_hidden_manifest.jsonl")
    validation_errors = validate_inputs(fill_summary, packet_summary, filled_rows, hidden_rows)

    hidden_by_id = {row["review_id"]: row for row in hidden_rows}
    target_rows = [derive_targets(row, hidden_by_id[row["review_id"]]) for row in filled_rows]

    shortcut: list[dict[str, Any]] = []
    for name, field in [
        ("p_rel_binary", "p_rel_target"),
        ("c_e_compatibility_binary", "c_e_compatibility_target"),
        ("p_obs_binary", "p_obs_target"),
        ("q_e_observability_ordinal", "q_e_observability_ordinal"),
        ("relation_multiclass", "relation_multiclass_target"),
    ]:
        shortcut.extend(shortcut_rows(target_rows, field, name))
    viability = target_viability_rows(target_rows, shortcut)
    risks = risk_register_rows(viability)

    high_non_label_risks = [
        row for row in shortcut if row["risk"] == "high" and row["predictor_category"] != "label_derived"
    ]
    any_smoke_allowed = any(row["learned_smoke_allowed"] for row in viability)
    status = STATUS_READY if (not validation_errors and any_smoke_allowed and not high_non_label_risks) else STATUS_SHORTCUT_RISK
    if validation_errors:
        status = STATUS_ERROR
    next_todo = NEXT_TODO if not validation_errors else "repair_support_contact_visual_mesh_audit_label_ingestion"

    output_paths = {
        "c_e_binary_target": output_dir / "c_e_binary_target.jsonl",
        "model_input_boundary": output_dir / "model_input_boundary.json",
        "p_obs_target": output_dir / "p_obs_target.jsonl",
        "p_rel_binary_target": output_dir / "p_rel_binary_target.jsonl",
        "q_e_target": output_dir / "q_e_target.jsonl",
        "relation_multiclass_target": output_dir / "relation_multiclass_target.jsonl",
        "report": output_dir / "report.md",
        "risk_register": output_dir / "risk_register.csv",
        "shortcut_diagnostics": output_dir / "shortcut_diagnostics.csv",
        "summary": output_dir / "summary.json",
        "target_counts": output_dir / "target_counts.csv",
        "target_rows": output_dir / "target_rows.jsonl",
        "target_viability": output_dir / "target_viability.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    target_summary = {
        "rows": len(target_rows),
        "p_rel_binary_rows": sum(1 for row in target_rows if row["p_rel_target"] is not None),
        "p_rel_binary_counts": dict(Counter(str(row["p_rel_target"]) for row in target_rows if row["p_rel_target"] is not None)),
        "c_e_binary_rows": sum(1 for row in target_rows if row["c_e_compatibility_target"] is not None),
        "c_e_binary_counts": dict(
            Counter(str(row["c_e_compatibility_target"]) for row in target_rows if row["c_e_compatibility_target"] is not None)
        ),
        "p_obs_counts": dict(Counter(str(row["p_obs_target"]) for row in target_rows)),
        "relation_multiclass_counts": dict(Counter(row["relation_multiclass_target"] for row in target_rows)),
        "high_non_label_shortcut_predictors": sorted({row["predictor"] for row in high_non_label_risks}),
        "learned_smoke_allowed": any_smoke_allowed and not high_non_label_risks,
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "fill_status": fill_summary.get("status"),
        "packet_status": packet_summary.get("status"),
        "target_summary": target_summary,
        "target_viability": viability,
        "shortcut_summary": {
            "diagnostic_rows": len(shortcut),
            "high_non_label_risk_count": len(high_non_label_risks),
            "high_non_label_risk_predictors": target_summary["high_non_label_shortcut_predictors"],
        },
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_new_labels": False,
            "hidden_manifest_join_after_label_lock": True,
            "hidden_manifest_used_for_label_fill": False,
            "source_score_or_rank_used_for_label_fill": False,
            "old_geometry_used_for_label_fill": False,
            "label_provenance": "codex_visible_packet_proxy_labeler_user_requested",
            "independent_human_audit": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_jsonl(output_paths["target_rows"], target_rows)
    write_jsonl(output_paths["p_rel_binary_target"], target_jsonl(target_rows, "p_rel_target"))
    write_jsonl(output_paths["c_e_binary_target"], target_jsonl(target_rows, "c_e_compatibility_target"))
    write_jsonl(output_paths["p_obs_target"], target_jsonl(target_rows, "p_obs_target"))
    write_jsonl(output_paths["q_e_target"], target_jsonl(target_rows, "q_e_observability_ordinal"))
    write_jsonl(output_paths["relation_multiclass_target"], target_jsonl(target_rows, "relation_multiclass_target"))
    write_csv(output_paths["target_counts"], target_count_rows(target_rows))
    write_csv(output_paths["shortcut_diagnostics"], shortcut)
    write_csv(output_paths["target_viability"], viability)
    write_csv(output_paths["risk_register"], risks)
    write_json(
        output_paths["model_input_boundary"],
        {
            "allowed_model_inputs_after_future_feature_join": [
                "T_e predicate text/label",
                "subject/object class text only under class-pair control",
                "predicate-independent G_e features from packet/mesh/point features",
                "Q_e evidence availability features only if p_obs has non-degenerate labels",
            ],
            "blocked_model_inputs": [
                "construction_bucket_hidden",
                "hidden_stratum_hidden",
                "queue_kind_hidden",
                "geometry_status_hidden",
                "label_match_status_hidden",
                "p_geom_valid_hidden",
                "source_score_hidden",
                "source_rank_hidden",
                "decision_reason",
                "review_geometry_support as input to p_rel",
            ],
            "reason": "current proxy labels are shortcut-prone; hidden fields are audit/provenance only",
        },
    )
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
