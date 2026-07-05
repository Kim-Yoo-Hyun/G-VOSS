#!/usr/bin/env python3
"""Write the R6 supported-by decomposition train-only smoke plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_plan"

EXPECTED_AUDIT_STATUS = "h002_compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit_ready_for_smoke_plan"
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_supported_by_decomposition_smoke_plan"
EXPECTED_INPUT_SCHEMA = "h002_r6_supported_by_decomposition_smoke_ready_view_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_v1"
SMOKE_READY_SCHEMA = "h002_r6_supported_by_decomposition_runner_ready_view_v1"
STATUS_READY = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v3_supported_by_decomposition_smoke_runner"

EXPECTED_ROWS = 320
EXPECTED_LABEL_COUNTS = {
    "abstain": 80,
    "accept_broad_support": 80,
    "reject_no_support": 80,
    "relabel_to_subtype": 80,
}
EXPECTED_FEATURE_BLOCKS = {"G_e_mesh_pose_contact", "Q_e", "T_e"}
EXPECTED_P_OBS = {0: 80, 1: 240}
EXPECTED_P_REL_BINARY = {0: 80, 1: 160}
EXPECTED_P_REL_3WAY = {
    "accept_broad_support": 80,
    "reject_no_support": 80,
    "relabel_to_subtype": 80,
}

MEDIUM_RISK_MAX = 0.90
PRIMARY_OBS_AUROC_MIN = 0.80
PRIMARY_REL_AUROC_MIN = 0.65
PRIMARY_GAIN_MIN = 0.03
SHUFFLED_CONTROL_MARGIN = 0.05

LABEL_TO_ID = {
    "accept_broad_support": 0,
    "relabel_to_subtype": 1,
    "reject_no_support": 2,
    "abstain": 3,
}
P_REL_3WAY_TO_ID = {
    "accept_broad_support": 0,
    "relabel_to_subtype": 1,
    "reject_no_support": 2,
}

FORBIDDEN_FEATURE_PATH_FRAGMENTS = [
    "audit_status",
    "candidate_role",
    "construction",
    "directed_pair",
    "geometry_status",
    "h001",
    "hidden",
    "label_match",
    "machine_hint",
    "matched",
    "object_id",
    "p_geom",
    "prediction_id",
    "queue",
    "rank",
    "reason",
    "scan_id",
    "semantic_rank",
    "semantic_score",
    "source_id",
    "subgraph_id",
    "subject_id",
    "target_source",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: str, prefix: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def feature_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.append(child_prefix)
            paths.extend(feature_paths(child, child_prefix))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def numeric_value_count(rows: list[dict[str, Any]], path: str) -> tuple[int, int]:
    present = 0
    finite = 0
    for row in rows:
        value = nested_get(row, path)
        if value is None or value == "":
            continue
        present += 1
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            finite += 1
    return present, finite


def target_payload(label: str) -> dict[str, Any]:
    p_obs_y = 0 if label == "abstain" else 1
    if label == "abstain":
        p_rel_binary_y = None
        p_rel_3way_label = None
        p_rel_3way_id = None
    else:
        p_rel_binary_y = 0 if label == "reject_no_support" else 1
        p_rel_3way_label = label
        p_rel_3way_id = P_REL_3WAY_TO_ID[label]
    return {
        "target_decomposition_id": LABEL_TO_ID[label],
        "target_decomposition_label": label,
        "target_p_obs_y": p_obs_y,
        "target_p_rel_binary_y": p_rel_binary_y,
        "target_p_rel_3way_id": p_rel_3way_id,
        "target_p_rel_3way_label": p_rel_3way_label,
    }


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        label = str(row["target_label"])
        cv_group = nested_get(row, "split_metadata.cv_group_id") or row.get("cv_group_id")
        row_id = str(row["row_id"])
        normalized.append(
            {
                "example_id": stable_hash(row_id, "ex"),
                "feature_blocks": row["feature_blocks"],
                "row_id": row_id,
                "schema_version": SMOKE_READY_SCHEMA,
                "split": "train",
                "split_metadata": {
                    "cv_group_id": str(cv_group),
                    "group_use": "split_only_not_model_feature",
                },
                **target_payload(label),
            }
        )
    return normalized


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(str(row["target_decomposition_label"]) for row in rows)
    p_obs = Counter(int(row["target_p_obs_y"]) for row in rows)
    p_rel_binary = Counter(int(row["target_p_rel_binary_y"]) for row in rows if row["target_p_rel_binary_y"] is not None)
    p_rel_3way = Counter(str(row["target_p_rel_3way_label"]) for row in rows if row["target_p_rel_3way_label"] is not None)
    schemas = Counter(str(row.get("schema_version")) for row in rows)
    blocks = Counter(tuple(sorted(row.get("feature_blocks", {}).keys())) for row in rows)
    cv_groups: dict[str, list[str]] = defaultdict(list)
    class_pairs = Counter(
        f"{nested_get(row, 'feature_blocks.T_e.subject_class_text')}->{nested_get(row, 'feature_blocks.T_e.object_class_text')}"
        for row in rows
    )
    observability = Counter(str(nested_get(row, "feature_blocks.Q_e.observability_status")) for row in rows)
    geometry_contradiction = Counter(str(nested_get(row, "feature_blocks.Q_e.geometry_contradiction")) for row in rows)
    for row in rows:
        cv_groups[str(nested_get(row, "split_metadata.cv_group_id"))].append(str(row["target_decomposition_label"]))
    return {
        "class_pairs": len(class_pairs),
        "cv_groups": len(cv_groups),
        "feature_block_sets": {",".join(key): count for key, count in sorted(blocks.items())},
        "geometry_contradiction_counts": dict(sorted(geometry_contradiction.items())),
        "label_counts": dict(sorted(labels.items())),
        "max_rows_per_cv_group": max((len(values) for values in cv_groups.values()), default=0),
        "mixed_label_cv_groups": sum(1 for values in cv_groups.values() if len(set(values)) >= 2),
        "observability_counts": dict(sorted(observability.items())),
        "p_obs_counts": dict(sorted(p_obs.items())),
        "p_rel_3way_counts": dict(sorted(p_rel_3way.items())),
        "p_rel_binary_counts": dict(sorted(p_rel_binary.items())),
        "rows": len(rows),
        "schema_versions": dict(sorted(schemas.items())),
        "top_class_pairs": dict(class_pairs.most_common(10)),
    }


def validate_inputs(audit_summary: dict[str, Any], raw_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]], audit_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if int(audit_summary.get("validation_errors", -1)) != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    counts = audit_summary.get("counts", {})
    if counts.get("schema_leakage_hits") != 0 or counts.get("allowed_high_risk_probes") != 0:
        errors.append({"error_type": "audit_not_schema_clean", "counts": counts})
    if counts.get("smoke_ready_rows") != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_audit_smoke_ready_rows", "actual": counts.get("smoke_ready_rows")})
    if counts.get("label_counts") != EXPECTED_LABEL_COUNTS:
        errors.append({"error_type": "unexpected_audit_label_counts", "actual": counts.get("label_counts")})
    validation_path = audit_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors_file", "path": rel_path(validation_path)})

    raw_schema_counts = Counter(str(row.get("schema_version")) for row in raw_rows)
    if raw_schema_counts != Counter({EXPECTED_INPUT_SCHEMA: EXPECTED_ROWS}):
        errors.append({"error_type": "unexpected_raw_schema_counts", "actual": dict(raw_schema_counts)})

    row_counts = count_summary(smoke_rows)
    if row_counts["rows"] != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_row_count", **row_counts})
    if row_counts["label_counts"] != EXPECTED_LABEL_COUNTS:
        errors.append({"error_type": "unexpected_label_counts", **row_counts})
    if row_counts["p_obs_counts"] != EXPECTED_P_OBS:
        errors.append({"error_type": "unexpected_p_obs_counts", **row_counts})
    if row_counts["p_rel_binary_counts"] != EXPECTED_P_REL_BINARY:
        errors.append({"error_type": "unexpected_p_rel_binary_counts", **row_counts})
    if row_counts["p_rel_3way_counts"] != EXPECTED_P_REL_3WAY:
        errors.append({"error_type": "unexpected_p_rel_3way_counts", **row_counts})
    if row_counts["schema_versions"] != {SMOKE_READY_SCHEMA: EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_smoke_schema_versions", **row_counts})
    if row_counts["feature_block_sets"] != {"G_e_mesh_pose_contact,Q_e,T_e": EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_feature_block_sets", **row_counts})

    for row in smoke_rows:
        paths = feature_paths(row.get("feature_blocks", {}), "feature_blocks")
        for path in paths:
            lower = path.lower()
            for token in FORBIDDEN_FEATURE_PATH_FRAGMENTS:
                if token in lower:
                    errors.append({"error_type": "forbidden_feature_path", "row_id": row.get("row_id"), "path": path, "token": token})
        for field in [
            "feature_blocks.G_e_mesh_pose_contact.abs_surface_gap_subject_bottom_to_object_top",
            "feature_blocks.G_e_mesh_pose_contact.center_delta_z",
            "feature_blocks.G_e_mesh_pose_contact.obb_contact_likelihood_proxy",
            "feature_blocks.G_e_mesh_pose_contact.support_area_proxy",
            "feature_blocks.G_e_mesh_pose_contact.xy_overlap_min_ratio",
        ]:
            value = nested_get(row, field)
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                errors.append({"error_type": "non_finite_required_geometry_feature", "row_id": row.get("row_id"), "field": field, "value": value})
    return errors


def input_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        "feature_blocks.T_e.predicate_label",
        "feature_blocks.T_e.predicate_family",
        "feature_blocks.T_e.subject_class_text",
        "feature_blocks.T_e.object_class_text",
        "feature_blocks.Q_e.observability_status",
        "feature_blocks.Q_e.geometry_contradiction",
        "feature_blocks.Q_e.generic_endpoint_visible",
        "feature_blocks.Q_e.mesh_semseg_obb_available",
        "feature_blocks.G_e_mesh_pose_contact.abs_surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_mesh_pose_contact.center_delta_z",
        "feature_blocks.G_e_mesh_pose_contact.center_distance_xy",
        "feature_blocks.G_e_mesh_pose_contact.normalized_center_distance_xy",
        "feature_blocks.G_e_mesh_pose_contact.obb_contact_likelihood_proxy",
        "feature_blocks.G_e_mesh_pose_contact.object_flatness_ratio",
        "feature_blocks.G_e_mesh_pose_contact.subject_flatness_ratio",
        "feature_blocks.G_e_mesh_pose_contact.support_area_proxy",
        "feature_blocks.G_e_mesh_pose_contact.surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_mesh_pose_contact.xy_overlap_min_ratio",
        "feature_blocks.G_e_mesh_pose_contact.xy_overlap_object_ratio",
        "feature_blocks.G_e_mesh_pose_contact.xy_overlap_subject_ratio",
    ]
    out: list[dict[str, Any]] = []
    for path in paths:
        values = [nested_get(row, path) for row in rows]
        missing = sum(1 for value in values if value is None or value == "")
        distinct = len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        present, finite = numeric_value_count(rows, path)
        out.append(
            {
                "distinct_values": distinct,
                "feature_path": path,
                "finite_numeric": finite,
                "missing": missing,
                "present": present,
                "rows": len(rows),
                "usable_as_feature": True,
            }
        )
    return out


def feature_path_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = sorted({path for row in rows for path in feature_paths(row.get("feature_blocks", {}), "feature_blocks")})
    return [{"feature_path": path, "model_input_allowed": True} for path in paths]


def task_rows() -> list[dict[str, Any]]:
    return [
        {
            "task": "T0_decomposition_4way",
            "rows": 320,
            "target_field": "target_decomposition_id",
            "target_semantics": "accept_broad_support / relabel_to_subtype / reject_no_support / abstain",
            "primary": False,
            "metric": "macro_F1, balanced_accuracy, one-vs-rest AUROC",
        },
        {
            "task": "T1_p_obs_binary",
            "rows": 320,
            "target_field": "target_p_obs_y",
            "target_semantics": "observable route decision versus abstain",
            "primary": True,
            "metric": "AUROC, AUPRC, balanced_accuracy, calibration",
        },
        {
            "task": "T2_p_rel_binary_observable",
            "rows": 240,
            "target_field": "target_p_rel_binary_y",
            "target_semantics": "observable accept-or-relabel versus reject_no_support",
            "primary": True,
            "metric": "AUROC, AUPRC, balanced_accuracy, calibration",
        },
        {
            "task": "T3_p_rel_3way_observable",
            "rows": 240,
            "target_field": "target_p_rel_3way_id",
            "target_semantics": "accept_broad_support / relabel_to_subtype / reject_no_support among observable rows",
            "primary": False,
            "metric": "macro_F1, balanced_accuracy, one-vs-rest AUROC",
        },
    ]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {"model": "M0_prior", "input_blocks": "none", "primary": False, "role": "class-balance sanity baseline", "tasks": "T0,T1,T2,T3"},
        {"model": "M1_T_class_only", "input_blocks": "T_e", "primary": False, "role": "semantic/class-pair shortcut baseline", "tasks": "T0,T1,T2,T3"},
        {"model": "M2_G_geometry_only", "input_blocks": "G_e_mesh_pose_contact", "primary": False, "role": "geometry-only support/contact evidence baseline", "tasks": "T0,T1,T2,T3"},
        {"model": "M3_Q_observability_only", "input_blocks": "Q_e", "primary": False, "role": "observability-only baseline; expected strong for p_obs only", "tasks": "T0,T1,T2,T3"},
        {"model": "M4_TG_concat", "input_blocks": "T_e + G_e_mesh_pose_contact", "primary": False, "role": "semantic plus geometry concat without explicit route head", "tasks": "T0,T2,T3"},
        {"model": "M5_GQ_route", "input_blocks": "G_e_mesh_pose_contact + Q_e", "primary": False, "role": "route evidence with observability but no class semantics", "tasks": "T0,T1,T2,T3"},
        {"model": "M6_TGQ_factorized_route", "input_blocks": "T_e + G_e_mesh_pose_contact + Q_e", "primary": True, "role": "primary R6 factorized route smoke", "tasks": "T0,T1,T2,T3"},
        {"model": "S1_subject_object_class_pair", "input_blocks": "T_e.subject_class_text + T_e.object_class_text", "primary": False, "role": "allowed class-pair shortcut probe", "tasks": "T0,T1,T2,T3"},
        {"model": "S2_single_G_e_best_feature", "input_blocks": "one G_e scalar at a time", "primary": False, "role": "single geometry-feature shortcut probe", "tasks": "T0,T1,T2,T3"},
        {"model": "S3_Q_only_for_p_rel", "input_blocks": "Q_e only on observable rows", "primary": False, "role": "Q_e should not solve p_rel after abstain rows are removed", "tasks": "T2,T3"},
        {"model": "H1_hidden_source_rank_probe", "input_blocks": "hidden semantic_score/rank/p_geom_valid only", "primary": False, "role": "audit-only leakage risk, not model input", "tasks": "T0,T1,T2,T3"},
        {"model": "H2_hidden_construction_probe", "input_blocks": "hidden label_match/machine_hint/matched_predicates/evidence_reason only", "primary": False, "role": "audit-only leakage risk, not model input", "tasks": "T0,T1,T2,T3"},
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {"control": "shuffled_G_global", "construction": "permute G_e_mesh_pose_contact across all rows", "expected_result": "route evidence alignment should degrade"},
        {"control": "shuffled_G_within_class_pair", "construction": "permute G_e within subject/object class-pair cells where possible", "expected_result": "preserves class-pair distribution while breaking paired geometry"},
        {"control": "shuffled_Q_global", "construction": "permute Q_e across all rows", "expected_result": "p_obs should degrade if observability is real"},
        {"control": "no_Q_for_p_obs", "construction": "compare p_obs with and without Q_e", "expected_result": "p_obs should rely on Q_e, not T_e alone"},
        {"control": "Q_only_for_p_rel", "construction": "run Q_e-only on observable p_rel rows", "expected_result": "Q_e should not define relation truth after abstain removal"},
        {"control": "hidden_source_rank_audit", "construction": "run source score/rank/p_geom_valid as audit-only probes", "expected_result": "reported as leakage risk, never as allowed model"},
        {"control": "hidden_construction_audit", "construction": "run label_match/machine_hint/matched_predicates/evidence_reason as audit-only probes", "expected_result": "should remain excluded even if predictive"},
        {"control": "class_pair_slice", "construction": "report per-class-pair majority and slice metrics", "expected_result": "prevents class-pair memorization overclaim"},
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {"gate": "data_integrity", "criterion": "rows=320; decomposition labels 80/80/80/80; p_obs 240/80; observable p_rel rows=240", "blocks_runner_if_fail": True},
        {"gate": "schema_safety", "criterion": "runner reads only smoke_ready_view feature_blocks and target fields; hidden manifests stay excluded", "blocks_runner_if_fail": True},
        {"gate": "medium_shortcut_boundary", "criterion": f"allowed single-factor controls above {MEDIUM_RISK_MAX:.2f} trigger path decision", "blocks_promotion_if_fail": True},
        {"gate": "p_obs_signal", "criterion": f"T1 primary p_obs AUROC >= {PRIMARY_OBS_AUROC_MIN:.2f}; Q_e may be dominant by design", "blocks_promotion_if_fail": True},
        {"gate": "p_rel_signal", "criterion": f"T2 primary p_rel AUROC >= {PRIMARY_REL_AUROC_MIN:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "p_rel_gain", "criterion": f"M6_TGQ beats max(M1_T, M2_G, M3_Q) by >= {PRIMARY_GAIN_MIN:.2f} on T2 or else report simpler route", "blocks_paper_claim_if_fail": True},
        {"gate": "Q_e_boundary", "criterion": "Q_e-only should not solve observable p_rel; if it does, label target is observability rather than reliability", "blocks_paper_claim_if_fail": True},
        {"gate": "shuffled_G_degradation", "criterion": f"shuffled-G controls should not match primary within {SHUFFLED_CONTROL_MARGIN:.2f} AUROC on T2/T3", "blocks_promotion_if_fail": True},
        {"gate": "hidden_probe_boundary", "criterion": "hidden construction/source probes may be high but must be reported as leakage risk only", "blocks_runner_if_fail": False},
        {"gate": "paper_boundary", "criterion": "train-only hypothesis smoke; Docker reproduction and held-out protocol required before paper evidence", "blocks_paper_evidence": True},
    ]


def smoke_plan(input_path: Path) -> dict[str, Any]:
    return {
        "controls": control_rows(),
        "feature_engineering": {
            "G_e_mesh_pose_contact": "predicate-independent semseg OBB mesh/pose/contact geometry evidence",
            "Q_e": "observability and evidence-quality fields; allowed for p_obs and as a diagnostic factor, not as truth",
            "T_e": "supported-by predicate text/family and subject/object class text",
            "Z_e_policy": "source confidence, rank, queue, p_geom_valid, and GT match fields remain hidden and excluded",
            "primary_route": "decompose broad supported-by into accept, relabel, reject, and abstain heads",
        },
        "gates": gate_rows(),
        "input_contract": {
            "allowed_blocks": sorted(EXPECTED_FEATURE_BLOCKS),
            "feature_root": "feature_blocks",
            "forbidden_feature_path_fragments": FORBIDDEN_FEATURE_PATH_FRAGMENTS,
            "group_key": "split_metadata.cv_group_id",
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "metadata_only": ["row_id", "example_id", "schema_version", "split", "split_metadata"],
            "row_count": EXPECTED_ROWS,
            "target_fields": [
                "target_decomposition_id",
                "target_decomposition_label",
                "target_p_obs_y",
                "target_p_rel_binary_y",
                "target_p_rel_3way_id",
                "target_p_rel_3way_label",
            ],
        },
        "metrics": ["AUROC", "AUPRC", "macro_F1", "balanced_accuracy", "Brier", "ECE", "fold mean/std", "slice metrics"],
        "models": model_view_rows(),
        "paper_boundary": {
            "docker_required_before_paper_promotion": True,
            "hypothesis_stage_only": True,
            "paper_evidence_allowed": False,
        },
        "schema_version": SCHEMA_VERSION,
        "split_policy": {
            "folds": 5,
            "group_key": "split_metadata.cv_group_id",
            "group_rule": "same scan hash stays in the same fold",
            "split": "train_internal_grouped_cv",
            "test_usage": False,
            "validation_usage": False,
        },
        "tasks": task_rows(),
    }


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 R6 Supported-By Decomposition Smoke Plan

## Status

```text
artifact_root = {summary["output_paths"]["artifact_root"]}
status = {summary["status"]}
rows = {counts["rows"]}
label_counts = {json.dumps(counts["label_counts"], ensure_ascii=False, sort_keys=True)}
p_obs_counts = {json.dumps(counts["p_obs_counts"], ensure_ascii=False, sort_keys=True)}
p_rel_binary_counts = {json.dumps(counts["p_rel_binary_counts"], ensure_ascii=False, sort_keys=True)}
cv_groups = {counts["cv_groups"]}
mixed_label_cv_groups = {counts["mixed_label_cv_groups"]}
validation_errors = {summary["validation_errors"]}
learned_smoke_executed = false
next_todo = {summary["next_todo"]}
```

## Planned Tasks

- `T0_decomposition_4way`: accept / relabel / reject / abstain.
- `T1_p_obs_binary`: observable versus abstain.
- `T2_p_rel_binary_observable`: accept-or-relabel versus reject, excluding abstain.
- `T3_p_rel_3way_observable`: accept / relabel / reject among observable rows.

## Planned Main Comparison

- `M1_T_class_only`
- `M2_G_geometry_only`
- `M3_Q_observability_only`
- `M4_TG_concat`
- `M5_GQ_route`
- `M6_TGQ_factorized_route` as the primary route smoke

## Required Controls

- shuffled-G global
- shuffled-G within class-pair
- shuffled-Q
- Q-only for observable p_rel
- class-pair slice metrics
- hidden source/rank/p_geom audit probes
- hidden construction-field audit probes

## Interpretation

This step does not train a model. It freezes the train-only smoke input and
comparison contract for R6 `supported by`. The runner must use only
`T_e`, `G_e_mesh_pose_contact`, and `Q_e` feature blocks. Hidden construction
fields, source score/rank, H001 `p_geom_valid`, GT match fields, and audit
reasons remain outside model input.
"""


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    raw_rows = read_jsonl(args.audit_dir / "smoke_ready_view.jsonl")
    smoke_rows = normalize_rows(raw_rows)
    validation_errors = validate_inputs(audit_summary, raw_rows, smoke_rows, args.audit_dir)
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    next_todo = NEXT_TODO if not validation_errors else "compatibility_dataset_v3_supported_by_decomposition_smoke_plan_repair"

    input_path = args.output_dir / "smoke_ready_view.jsonl"
    write_jsonl(input_path, smoke_rows)
    counts = count_summary(smoke_rows)
    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "control_plan": rel_path(args.output_dir / "control_plan.csv"),
        "feature_paths": rel_path(args.output_dir / "feature_paths.csv"),
        "gate_plan": rel_path(args.output_dir / "gate_plan.csv"),
        "input_manifest": rel_path(args.output_dir / "input_manifest.json"),
        "input_profile": rel_path(args.output_dir / "input_profile.csv"),
        "model_views": rel_path(args.output_dir / "model_views.csv"),
        "report": rel_path(args.output_dir / "report.md"),
        "smoke_plan": rel_path(args.output_dir / "smoke_plan.json"),
        "smoke_ready_view": rel_path(input_path),
        "summary": rel_path(args.output_dir / "summary.json"),
        "task_plan": rel_path(args.output_dir / "task_plan.csv"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_new_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_smoke_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "audit_smoke_ready_view": rel_path(args.audit_dir / "smoke_ready_view.jsonl"),
            "audit_summary": rel_path(args.audit_dir / "summary.json"),
        },
        "learned_smoke_executed": False,
        "next_todo": next_todo,
        "output_paths": output_paths,
        "primary_model": "M6_TGQ_factorized_route",
        "schema_version": SCHEMA_VERSION,
        "smoke_runner_implementation_allowed": not validation_errors,
        "status": status,
        "validation_errors": len(validation_errors),
    }
    input_manifest = {
        "input_rows": counts["rows"],
        "input_sha256": sha256_file(input_path),
        "runner_ready_schema": SMOKE_READY_SCHEMA,
        "schema_version": "h002_r6_supported_by_decomposition_smoke_input_manifest_v1",
        "source_audit_smoke_ready_view": rel_path(args.audit_dir / "smoke_ready_view.jsonl"),
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
    }

    write_csv(args.output_dir / "control_plan.csv", control_rows())
    write_csv(args.output_dir / "feature_paths.csv", feature_path_rows(smoke_rows))
    write_csv(args.output_dir / "gate_plan.csv", gate_rows())
    write_json(args.output_dir / "input_manifest.json", input_manifest)
    write_csv(args.output_dir / "input_profile.csv", input_profile_rows(smoke_rows))
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_json(args.output_dir / "smoke_plan.json", smoke_plan(input_path))
    write_csv(args.output_dir / "task_plan.csv", task_rows())
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
