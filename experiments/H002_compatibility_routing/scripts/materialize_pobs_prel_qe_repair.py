#!/usr/bin/env python3
"""Materialize repaired Q_e v2 views for H002 p_obs / p_rel diagnostics."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_pobs_prel_qe_repair_materialization_v1"
STATUS_READY = "h002_pobs_prel_qe_repair_materialization_ready"
STATUS_ERROR = "h002_pobs_prel_qe_repair_materialization_errors"
EXPECTED_PLAN_STATUS = "h002_pobs_prel_qe_repair_plan_ready"
EXPECTED_SOURCE_STATUS = "h002_pobs_prel_selective_materialization_ready"
EXPECTED_INGESTION_STATUS = "h002_pobs_prel_observability_label_ingestion_ready"
TRAIN_SPLIT = "internal_train"

BLOCKED_LEAF_KEYS = {
    "observability_label",
    "obs_label",
    "rel_label",
    "decision_label",
    "p_obs_target_after_audit",
    "p_rel_target_after_audit",
    "label_status",
    "label_provenance",
    "external_reviewer_id",
    "target_y",
    "gt_match",
    "p_geom_valid",
    "queue_kind",
    "repair_role",
    "codex_seed_hint_not_gt",
    "label_rationale",
    "hidden_observability_labels",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--repair-plan-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_qe_repair_plan/latest"),
    )
    parser.add_argument(
        "--source-materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_materialization/latest"),
    )
    parser.add_argument(
        "--observability-ingestion-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_observability_ingestion/latest"),
    )
    parser.add_argument(
        "--observability-label-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_observability_labels/latest"),
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_rank(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    blocks = row.get("feature_blocks")
    return blocks if isinstance(blocks, dict) else {}


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("Q_e", {})
    return copy.deepcopy(block) if isinstance(block, dict) else {}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        out = float(value)
    except (TypeError, ValueError):
        return default
    if out != out:
        return default
    return out


def source_quality(q: dict[str, Any]) -> dict[str, Any]:
    safe = q.get("Q_e_safe", {}) if isinstance(q.get("Q_e_safe"), dict) else {}
    obs = q.get("Q_e_observability", {}) if isinstance(q.get("Q_e_observability"), dict) else {}
    raw_available = bool(safe.get("raw_geometry_available", q.get("geometry_observable", True)))
    coverage = safe_float(safe.get("object_pair_feature_coverage"), 1.0 if raw_available else 0.0)
    feature_count = safe_float(safe.get("raw_geometry_feature_count"), 14.0 if raw_available else 0.0)
    mesh_availability = str(safe.get("mesh_or_point_availability") or q.get("geometry_quality_flag") or "available")
    return {
        "raw_available": raw_available,
        "coverage": max(0.0, min(1.0, coverage)),
        "feature_count": max(0.0, feature_count),
        "mesh_availability": mesh_availability,
        "source_state_code": safe_float(obs.get("q_e_state_code"), 1.0 if raw_available else 0.0),
    }


def state_spec(state: str) -> dict[str, Any]:
    specs = {
        "sufficient": {
            "state_code": 1.0,
            "sufficient": 1,
            "limited": 0,
            "ambiguous": 0,
            "missing": 0,
            "visual": 1.0,
            "geometry": 1.0,
            "ambiguity": 0.0,
        },
        "limited": {
            "state_code": 0.65,
            "sufficient": 0,
            "limited": 1,
            "ambiguous": 0,
            "missing": 0,
            "visual": 0.45,
            "geometry": 0.65,
            "ambiguity": 0.35,
        },
        "ambiguous": {
            "state_code": 0.35,
            "sufficient": 0,
            "limited": 0,
            "ambiguous": 1,
            "missing": 0,
            "visual": 0.50,
            "geometry": 0.50,
            "ambiguity": 1.0,
        },
        "missing": {
            "state_code": 0.0,
            "sufficient": 0,
            "limited": 0,
            "ambiguous": 0,
            "missing": 1,
            "visual": 0.0,
            "geometry": 0.0,
            "ambiguity": 0.0,
        },
    }
    return specs[state]


def repaired_qe(q: dict[str, Any], state: str, evidence_kind: str) -> dict[str, Any]:
    quality = source_quality(q)
    spec = state_spec(state)
    raw_available = quality["raw_available"] and state != "missing"
    coverage = quality["coverage"] * spec["geometry"]
    feature_count_norm = min(1.0, quality["feature_count"] / 14.0) * spec["geometry"]
    mesh_status = quality["mesh_availability"]
    if state == "missing":
        mesh_status = "missing_or_insufficient"
    elif state == "ambiguous":
        mesh_status = "ambiguous_support_pose_proxy"
    elif state == "limited":
        mesh_status = "limited_visibility_or_shuffled_proxy"
    out = {
        "Q_e_asset_availability": {
            "q_e_asset_raw_geometry_available": 1 if raw_available else 0,
            "q_e_asset_mesh_or_semseg_available": 1 if raw_available else 0,
            "q_e_asset_obb_pair_available": 1 if raw_available else 0,
            "q_e_asset_point_pair_crop_possible": 1 if raw_available and state in {"sufficient", "ambiguous", "limited"} else 0,
            "q_e_asset_missing_mesh_proxy": 1 if state == "missing" else 0,
        },
        "Q_e_visual_coverage": {
            "q_e_visual_cov_score": spec["visual"],
            "q_e_visual_cov_sufficient": 1 if state == "sufficient" else 0,
            "q_e_visual_cov_limited": 1 if state == "limited" else 0,
            "q_e_visual_no_view_proxy": 1 if evidence_kind == "no_view_control" else 0,
            "q_e_visual_shuffled_view_proxy": 1 if evidence_kind == "shuffled_view_control" else 0,
        },
        "Q_e_geometry_quality": {
            "q_e_geometry_feature_coverage": coverage,
            "q_e_geometry_feature_count_norm": feature_count_norm,
            "q_e_contact_surface_proxy_available": 1 if raw_available and state != "missing" else 0,
            "q_e_support_pose_proxy_available": 1 if state in {"sufficient", "ambiguous"} else 0,
            "q_e_geometry_quality_score": min(1.0, (coverage + feature_count_norm) / 2.0),
        },
        "Q_e_ambiguity": {
            "q_e_ambiguity_score": spec["ambiguity"],
            "q_e_pose_ambiguity_proxy": 1 if state == "ambiguous" else 0,
            "q_e_subtype_overflow_proxy": 1 if evidence_kind == "subtype_overflow_proxy" else 0,
            "q_e_weak_support_proxy": 1 if evidence_kind == "weak_support_proxy" else 0,
        },
        "Q_e_state_v2": {
            "q_e_state_code_v2": spec["state_code"],
            "q_e_state_sufficient_v2": spec["sufficient"],
            "q_e_state_limited_v2": spec["limited"],
            "q_e_state_ambiguous_v2": spec["ambiguous"],
            "q_e_state_missing_v2": spec["missing"],
        },
        # Backward-compatible keys for existing p_obs feature extractors.
        "Q_e_observability": {
            "q_e_state_code": spec["state_code"],
            "q_e_state_sufficient": spec["sufficient"],
            "q_e_state_limited": spec["limited"],
            "q_e_state_uncertain": 1 if state in {"ambiguous", "missing"} else 0,
            "q_e_state_ambiguous": spec["ambiguous"],
            "q_e_state_missing": spec["missing"],
        },
        "Q_e_safe": {
            "raw_geometry_available": raw_available,
            "object_pair_feature_coverage": coverage,
            "raw_geometry_feature_count": int(round(feature_count_norm * 14.0)),
            "mesh_or_point_availability": mesh_status,
        },
        "qe_v2_diagnostic_source": {
            "audit_proxy_used": 1 if evidence_kind.startswith(("audit_", "weak_", "subtype_")) else 0,
            "synthetic_control_used": 1 if evidence_kind.endswith("_control") else 0,
            "paper_promotion_allowed": 0,
        },
    }
    return out


def train_state_from_control(control_type: str) -> tuple[str, str, str, int, int | None, str]:
    if control_type == "observed_original":
        return "sufficient", "observed_original", "observable_clear", 1, None, "observed_original"
    if control_type == "low_visibility_control":
        return "limited", "low_visibility_control", "ambiguous_evidence", 0, None, "synthetic_limited_control"
    if control_type == "shuffled_view_control":
        return "ambiguous", "shuffled_view_control", "ambiguous_evidence", 0, None, "synthetic_ambiguity_control"
    if control_type in {"no_view_control", "missing_mesh_control"}:
        return "missing", control_type, "unobservable_missing_evidence", 0, None, "synthetic_missing_control"
    return "limited", "unknown_control", "ambiguous_evidence", 0, None, "synthetic_unknown_control"


def eval_state_from_audit_proxy(label_row: dict[str, Any]) -> tuple[str, str]:
    text = " ".join(
        str(label_row.get(key) or "")
        for key in ["repair_role", "queue_kind", "codex_seed_hint_not_gt", "label_rationale", "audit_question"]
    ).lower()
    if "weak_support" in text or "weak support" in text or "insufficient" in text:
        return "missing", "weak_support_proxy"
    if "explicitly ambiguous" in text or "lacks controlled subtype contrast" in text or "confound" in text:
        return "ambiguous", "audit_pose_or_subtype_ambiguity_proxy"
    if "low visibility" in text or "shuffled" in text:
        return "limited", "audit_limited_visibility_proxy"
    if "controlled class-pair context" in text:
        return "sufficient", "subtype_overflow_proxy"
    if "control rows are intended" in text or "observable control" in text:
        return "sufficient", "audit_observable_control_proxy"
    return "limited", "audit_fallback_limited_proxy"


def decision_label(obs_label: int, rel_label: int | None) -> str:
    if obs_label == 0:
        return "abstain"
    return "accept" if int(rel_label or 0) == 1 else "reject"


def label_rel_value(hidden: dict[str, Any], default: int | None = None) -> int | None:
    rel = hidden.get("rel_label")
    if rel is None:
        return default
    return int(rel)


def model_safe_qe(row: dict[str, Any], qe_v2: dict[str, Any], split: str) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_qe_v2_view",
        "candidate_id": row.get("candidate_id"),
        "source_candidate_id": row.get("source_candidate_id", row.get("candidate_id")),
        "eval_split": split,
        "route_family": row.get("route_family"),
        "predicate_label": row.get("predicate_label"),
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "control_type": row.get("control_type"),
        "row_role": row.get("row_role"),
        "feature_blocks": {"Q_e": qe_v2},
        "feature_use_policy": {
            "allowed_blocks": ["Q_e"],
            "blocked_blocks": ["T_e", "G_e", "Z_e", "hidden_observability_v2_labels"],
            "blocked_fields": sorted(BLOCKED_LEAF_KEYS),
            "label_fields_excluded": True,
        },
    }


def model_safe_prel(row: dict[str, Any], qe_v2: dict[str, Any], split: str) -> dict[str, Any]:
    blocks = copy.deepcopy(feature_blocks(row))
    blocks["Q_e"] = qe_v2
    return {
        "schema_version": f"{SCHEMA_VERSION}_prel_v2_view",
        "candidate_id": row.get("candidate_id"),
        "source_candidate_id": row.get("source_candidate_id", row.get("candidate_id")),
        "eval_split": split,
        "route_family": row.get("route_family"),
        "predicate_label": row.get("predicate_label"),
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "control_type": row.get("control_type"),
        "row_role": row.get("row_role"),
        "feature_blocks": blocks,
        "feature_use_policy": {
            "allowed_blocks": sorted(blocks),
            "blocked_fields": sorted(BLOCKED_LEAF_KEYS),
            "label_fields_excluded": True,
        },
    }


def hidden_label(
    row: dict[str, Any],
    split: str,
    observability_label: str,
    obs_label: int,
    rel_label: int | None,
    state: str,
    source: str,
    provenance: str,
) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_hidden_labels",
        "candidate_id": row.get("candidate_id"),
        "source_candidate_id": row.get("source_candidate_id", row.get("candidate_id")),
        "eval_split": split,
        "route_family": row.get("route_family"),
        "predicate_label": row.get("predicate_label"),
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "control_type": row.get("control_type"),
        "row_role": row.get("row_role"),
        "observability_label": observability_label,
        "obs_label": obs_label,
        "rel_label": rel_label,
        "decision_label": decision_label(obs_label, rel_label),
        "q_e_state_v2_hidden": state,
        "q_e_state_source_hidden": source,
        "label_only": True,
        "label_provenance": provenance,
        "target_policy": "hidden labels; model-safe Q_e v2 views exclude labels and raw audit fields",
    }


def flatten_keys(prefix: str, value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten_keys(f"{prefix}.{key}" if prefix else str(key), child)
    elif isinstance(value, list):
        yield prefix
    else:
        yield prefix


def blocked_hits(rows: list[dict[str, Any]], view: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        for flat_key in flatten_keys("", row):
            if flat_key.split(".")[-1] in BLOCKED_LEAF_KEYS:
                hits.append({"view": view, "candidate_id": row.get("candidate_id"), "blocked_key": flat_key})
    return hits


def state_from_qe(row: dict[str, Any]) -> str:
    state = (feature_blocks(row).get("Q_e", {}).get("Q_e_state_v2", {}) if isinstance(feature_blocks(row).get("Q_e"), dict) else {})
    if state.get("q_e_state_sufficient_v2"):
        return "sufficient"
    if state.get("q_e_state_limited_v2"):
        return "limited"
    if state.get("q_e_state_ambiguous_v2"):
        return "ambiguous"
    if state.get("q_e_state_missing_v2"):
        return "missing"
    return "unknown"


def balance_train_rows(joined: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    buckets: dict[str, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for item in joined:
        hidden = item[2]
        buckets[str(hidden["observability_label"])].append(item)
    if not buckets:
        return []
    target_n = min(len(rows) for rows in buckets.values())
    output: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for label, rows in sorted(buckets.items()):
        ordered = sorted(rows, key=lambda item: stable_rank(str(item[0].get("candidate_id")) + label))
        output.extend(ordered[:target_n])
    return sorted(output, key=lambda item: stable_rank(str(item[0].get("candidate_id"))))


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    plan_dir = resolve(repo_root, args.repair_plan_dir)
    source_dir = resolve(repo_root, args.source_materialization_dir)
    ingestion_dir = resolve(repo_root, args.observability_ingestion_dir)
    label_dir = resolve(repo_root, args.observability_label_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    plan = read_json(plan_dir / "summary.json")
    source_manifest = read_json(source_dir / "materialization_manifest.json")
    ingestion_manifest = read_json(ingestion_dir / "ingestion_manifest.json")
    label_summary = read_json(label_dir / "summary.json")
    if plan.get("status") != EXPECTED_PLAN_STATUS or plan.get("validation_errors") != 0:
        errors.append({"error_type": "repair_plan_not_ready", "status": plan.get("status"), "validation_errors": plan.get("validation_errors")})
    if source_manifest.get("status") != EXPECTED_SOURCE_STATUS or source_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "source_materialization_not_ready", "status": source_manifest.get("status")})
    if ingestion_manifest.get("status") != EXPECTED_INGESTION_STATUS or ingestion_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "observability_ingestion_not_ready", "status": ingestion_manifest.get("status")})

    source_qe = {row["candidate_id"]: row for row in read_jsonl(source_dir / "model_safe_qe_view.jsonl")}
    source_prel = {row["candidate_id"]: row for row in read_jsonl(source_dir / "model_safe_prel_view.jsonl")}
    source_hidden = {row["candidate_id"]: row for row in read_jsonl(source_dir / "hidden_selective_labels.jsonl")}
    eval_qe = {row["candidate_id"]: row for row in read_jsonl(ingestion_dir / "model_safe_qe_view.jsonl")}
    eval_prel = {row["candidate_id"]: row for row in read_jsonl(ingestion_dir / "model_safe_prel_view.jsonl")}
    eval_hidden = {row["candidate_id"]: row for row in read_jsonl(ingestion_dir / "hidden_observability_labels.jsonl")}
    label_rows = {row["candidate_id"]: row for row in read_jsonl(label_dir / "filled_observability_labels.jsonl")}

    train_joined: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for candidate_id, hidden in source_hidden.items():
        if hidden.get("eval_split") != TRAIN_SPLIT:
            continue
        qe_row = source_qe.get(candidate_id)
        prel_row = source_prel.get(candidate_id)
        if qe_row is None or prel_row is None:
            errors.append({"error_type": "missing_train_source_row", "candidate_id": candidate_id})
            continue
        state, evidence_kind, obs_label_name, obs_label, rel_override, role = train_state_from_control(str(hidden.get("control_type")))
        rel_label = label_rel_value(hidden, rel_override) if obs_label else None
        qe_v2 = repaired_qe(q_block(qe_row), state, evidence_kind)
        safe_qe = model_safe_qe({**qe_row, "row_role": role}, qe_v2, TRAIN_SPLIT)
        safe_prel = model_safe_prel({**prel_row, "row_role": role}, qe_v2, TRAIN_SPLIT)
        hidden_v2 = hidden_label(
            {**hidden, "row_role": role},
            TRAIN_SPLIT,
            obs_label_name,
            obs_label,
            rel_label,
            state,
            evidence_kind,
            "internal_train_control_or_observed_original_not_official_eval_label",
        )
        train_joined.append((safe_qe, safe_prel, hidden_v2))
    train_joined = balance_train_rows(train_joined)

    eval_qe_rows: list[dict[str, Any]] = []
    eval_prel_rows: list[dict[str, Any]] = []
    eval_hidden_rows: list[dict[str, Any]] = []
    for candidate_id in sorted(eval_hidden):
        qe_row = eval_qe.get(candidate_id)
        prel_row = eval_prel.get(candidate_id)
        hidden = eval_hidden[candidate_id]
        label_row = label_rows.get(candidate_id, {})
        if qe_row is None or prel_row is None or not label_row:
            errors.append({"error_type": "missing_eval_source_or_label_row", "candidate_id": candidate_id})
            continue
        state, evidence_kind = eval_state_from_audit_proxy(label_row)
        qe_v2 = repaired_qe(q_block(qe_row), state, evidence_kind)
        safe_qe = model_safe_qe(qe_row, qe_v2, "official_validation_diagnostic_subset")
        safe_prel = model_safe_prel(prel_row, qe_v2, "official_validation_diagnostic_subset")
        rel_label = hidden.get("rel_label")
        eval_hidden_rows.append(
            hidden_label(
                hidden,
                "official_validation_diagnostic_subset",
                str(hidden.get("observability_label")),
                int(hidden.get("obs_label")),
                int(rel_label) if rel_label is not None else None,
                state,
                evidence_kind,
                "user-confirmed Codex-filled audit labels; Q_e v2 state computed from audit proxy, not paper-level GT",
            )
        )
        eval_qe_rows.append(safe_qe)
        eval_prel_rows.append(safe_prel)

    train_qe_rows = [row[0] for row in train_joined]
    train_prel_rows = [row[1] for row in train_joined]
    train_hidden_rows = [row[2] for row in train_joined]
    hidden_all = train_hidden_rows + eval_hidden_rows
    all_model_rows = train_qe_rows + train_prel_rows + eval_qe_rows + eval_prel_rows
    hits = blocked_hits(all_model_rows, "model_safe_qe_or_prel_v2")
    if hits:
        errors.append({"error_type": "blocked_field_hits", "count": len(hits)})
    if not (len(train_qe_rows) == len(train_prel_rows) == len(train_hidden_rows)):
        errors.append(
            {
                "error_type": "train_row_count_mismatch",
                "qe": len(train_qe_rows),
                "prel": len(train_prel_rows),
                "hidden": len(train_hidden_rows),
            }
        )
    if not (len(eval_qe_rows) == len(eval_prel_rows) == len(eval_hidden_rows) == len(eval_hidden)):
        errors.append(
            {
                "error_type": "eval_row_count_mismatch",
                "qe": len(eval_qe_rows),
                "prel": len(eval_prel_rows),
                "hidden": len(eval_hidden_rows),
                "source_hidden": len(eval_hidden),
            }
        )

    eval_state_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    eval_sufficient_by_label: Counter[str] = Counter()
    eval_label_count: Counter[str] = Counter()
    for qe_row, label in zip(eval_qe_rows, eval_hidden_rows):
        obs_label = str(label["observability_label"])
        state = state_from_qe(qe_row)
        eval_state_by_label[obs_label][state] += 1
        eval_label_count[obs_label] += 1
        if state == "sufficient":
            eval_sufficient_by_label[obs_label] += 1
    for label in ["ambiguous_evidence", "unobservable_missing_evidence"]:
        if eval_label_count[label] and eval_sufficient_by_label[label] == eval_label_count[label]:
            errors.append({"error_type": "qe_label_alignment_failed", "observability_label": label})

    write_jsonl(out / "model_safe_qe_v2_train.jsonl", train_qe_rows)
    write_jsonl(out / "model_safe_prel_v2_train.jsonl", train_prel_rows)
    write_jsonl(out / "model_safe_qe_v2_eval.jsonl", eval_qe_rows)
    write_jsonl(out / "model_safe_prel_v2_eval.jsonl", eval_prel_rows)
    write_jsonl(out / "hidden_observability_v2_labels.jsonl", hidden_all)
    write_jsonl(out / "blocked_field_hits.jsonl", hits)
    write_jsonl(out / "validation_errors.jsonl", errors)

    train_balance_rows = [
        {"split": "train", "observability_label": key, "rows": value}
        for key, value in sorted(Counter(row["observability_label"] for row in train_hidden_rows).items())
    ]
    eval_balance_rows = [
        {"split": "eval", "observability_label": key, "rows": value}
        for key, value in sorted(Counter(row["observability_label"] for row in eval_hidden_rows).items())
    ]
    write_csv(out / "label_balance.csv", train_balance_rows + eval_balance_rows, ["split", "observability_label", "rows"])

    alignment_rows: list[dict[str, Any]] = []
    for label in sorted(eval_label_count):
        counts = eval_state_by_label[label]
        alignment_rows.append(
            {
                "split": "eval",
                "observability_label": label,
                "rows": eval_label_count[label],
                "q_e_state_sufficient_v2": counts.get("sufficient", 0),
                "q_e_state_limited_v2": counts.get("limited", 0),
                "q_e_state_ambiguous_v2": counts.get("ambiguous", 0),
                "q_e_state_missing_v2": counts.get("missing", 0),
            }
        )
    write_csv(out / "qe_v2_feature_alignment.csv", alignment_rows)

    source_rows = [
        {
            "source": "repair_plan",
            "path": repo_rel(repo_root, plan_dir),
            "status": plan.get("status"),
        },
        {
            "source": "source_materialization",
            "path": repo_rel(repo_root, source_dir),
            "status": source_manifest.get("status"),
        },
        {
            "source": "observability_ingestion",
            "path": repo_rel(repo_root, ingestion_dir),
            "status": ingestion_manifest.get("status"),
        },
        {
            "source": "observability_label_fill",
            "path": repo_rel(repo_root, label_dir),
            "status": label_summary.get("status"),
        },
    ]
    write_csv(out / "source_inputs.csv", source_rows)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "source_artifacts": {
            "repair_plan": repo_rel(repo_root, plan_dir),
            "source_materialization": repo_rel(repo_root, source_dir),
            "observability_ingestion": repo_rel(repo_root, ingestion_dir),
            "observability_label_fill": repo_rel(repo_root, label_dir),
        },
        "row_counts": {
            "train_qe_v2": len(train_qe_rows),
            "train_prel_v2": len(train_prel_rows),
            "eval_qe_v2": len(eval_qe_rows),
            "eval_prel_v2": len(eval_prel_rows),
            "hidden_labels_total": len(hidden_all),
            "train_label_counts": dict(sorted(Counter(row["observability_label"] for row in train_hidden_rows).items())),
            "eval_label_counts": dict(sorted(Counter(row["observability_label"] for row in eval_hidden_rows).items())),
            "eval_qe_state_by_label": {key: dict(sorted(value.items())) for key, value in sorted(eval_state_by_label.items())},
            "blocked_field_hits": len(hits),
        },
        "boundary": {
            "model_safe_views_exclude_hidden_labels": True,
            "raw_queue_kind_repair_role_seed_hint_excluded_from_model_safe": True,
            "eval_qe_v2_uses_audit_proxy": True,
            "paper_level_pobs_prel_solved_claim_allowed": False,
            "diagnostic_pobs_only_schema_audit_allowed": True,
            "official_test_used": False,
        },
        "decision": {
            "selected_path": "materialize_repaired_qe_v2_before_schema_audit",
            "next_todo": "pobs_prel_qe_repair_schema_audit",
        },
        "outputs": {
            "model_safe_qe_v2_train": repo_rel(repo_root, out / "model_safe_qe_v2_train.jsonl"),
            "model_safe_prel_v2_train": repo_rel(repo_root, out / "model_safe_prel_v2_train.jsonl"),
            "model_safe_qe_v2_eval": repo_rel(repo_root, out / "model_safe_qe_v2_eval.jsonl"),
            "model_safe_prel_v2_eval": repo_rel(repo_root, out / "model_safe_prel_v2_eval.jsonl"),
            "hidden_observability_v2_labels": repo_rel(repo_root, out / "hidden_observability_v2_labels.jsonl"),
            "label_balance": repo_rel(repo_root, out / "label_balance.csv"),
            "qe_v2_feature_alignment": repo_rel(repo_root, out / "qe_v2_feature_alignment.csv"),
            "blocked_field_hits": repo_rel(repo_root, out / "blocked_field_hits.jsonl"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "manifest": repo_rel(repo_root, out / "materialization_manifest.json"),
        },
    }
    write_json(out / "materialization_manifest.json", manifest)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
