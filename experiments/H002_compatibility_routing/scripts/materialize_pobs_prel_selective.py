#!/usr/bin/env python3
"""Materialize H002 p_obs / p_rel selective-decision views.

This materializer uses existing H002 internal/official materializations and
predeclared missing-evidence controls. It creates model-safe Q_e and p_rel
views plus hidden selective labels. It does not train models or compute metrics.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_pobs_prel_selective_materialization_v1"
STATUS_READY = "h002_pobs_prel_selective_materialization_ready"
STATUS_ERROR = "h002_pobs_prel_selective_materialization_errors"
EXPECTED_PROTOCOL_STATUS = "h002_pobs_prel_main_claim_protocol_after_report_0703_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_pobs_prel_materialization_plan_after_protocol"
CONTROL_TYPES = ["no_view_control", "low_visibility_control", "missing_mesh_control", "shuffled_view_control"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--internal-split-dir", type=Path, required=True)
    parser.add_argument("--official-materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
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


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    blocks = row.get("feature_blocks", {})
    return blocks if isinstance(blocks, dict) else {}


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    q = feature_blocks(row).get("Q_e", {})
    return copy.deepcopy(q) if isinstance(q, dict) else {}


def t_block(row: dict[str, Any]) -> dict[str, Any]:
    t = feature_blocks(row).get("T_e", {})
    return copy.deepcopy(t) if isinstance(t, dict) else {}


def g_block(row: dict[str, Any]) -> dict[str, Any]:
    g = feature_blocks(row).get("G_e", {})
    return copy.deepcopy(g) if isinstance(g, dict) else {}


def z_block(row: dict[str, Any]) -> dict[str, Any]:
    z = feature_blocks(row).get("Z_e", {})
    return copy.deepcopy(z) if isinstance(z, dict) else {}


def base_identity(row: dict[str, Any], eval_split: str) -> dict[str, Any]:
    return {
        "candidate_id": str(row.get("candidate_id") or row.get("unified_row_id")),
        "source_candidate_id": str(row.get("candidate_id") or row.get("unified_row_id")),
        "eval_split": eval_split,
        "route_family": row.get("route_family"),
        "predicate_label": row.get("predicate_label"),
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "control_type": "observed_original",
        "row_role": "real_observable",
    }


def original_q(q: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(q)
    out.setdefault("Q_e_safe", {})
    if isinstance(out["Q_e_safe"], dict):
        out["Q_e_safe"].setdefault("raw_geometry_available", bool(out.get("geometry_observable", True)))
        out["Q_e_safe"].setdefault("object_pair_feature_coverage", 1.0)
        out["Q_e_safe"].setdefault("mesh_or_point_availability", out.get("geometry_quality_flag", "available"))
    out.setdefault("Q_e_observability", {})
    if isinstance(out["Q_e_observability"], dict):
        out["Q_e_observability"].setdefault("q_e_state_code", 1.0)
        out["Q_e_observability"].setdefault("q_e_state_sufficient", 1)
        out["Q_e_observability"].setdefault("q_e_state_limited", 0)
        out["Q_e_observability"].setdefault("q_e_state_uncertain", 0)
    return out


def control_q(control_type: str) -> dict[str, Any]:
    base = {
        "geometry_observable": False,
        "mesh_or_semseg_available": False,
        "object_obb_available": False,
        "geometry_quality_flag": control_type,
        "synthetic_missing_evidence_control": True,
        "Q_e_safe": {
            "raw_geometry_available": False,
            "object_pair_feature_coverage": 0.0,
            "raw_geometry_feature_count": 0,
            "mesh_or_point_availability": "missing",
        },
        "Q_e_observability": {
            "q_e_state_code": 0.0,
            "q_e_state_sufficient": 0,
            "q_e_state_limited": 0,
            "q_e_state_uncertain": 1,
            "co_visible_view_count_proxy": 0.0,
            "min_subject_object_crop_count": 0.0,
            "min_subject_object_max_view_score": 0.0,
            "min_subject_object_total_image_count": 0.0,
            "multiview_packet_possible": 0,
            "point_pair_crop_possible": 0,
            "scan_asset_complete": 0,
            "subject_has_obb": 0,
            "object_has_obb": 0,
            "view_pair_mismatch_flag": 0,
        },
    }
    if control_type == "low_visibility_control":
        base["geometry_observable"] = True
        base["mesh_or_semseg_available"] = True
        base["object_obb_available"] = True
        base["Q_e_safe"]["raw_geometry_available"] = True
        base["Q_e_safe"]["object_pair_feature_coverage"] = 0.25
        base["Q_e_safe"]["raw_geometry_feature_count"] = 4
        base["Q_e_safe"]["mesh_or_point_availability"] = "low_visibility"
        base["Q_e_observability"]["q_e_state_code"] = 0.25
        base["Q_e_observability"]["q_e_state_limited"] = 1
        base["Q_e_observability"]["q_e_state_uncertain"] = 0
        base["Q_e_observability"]["subject_has_obb"] = 1
        base["Q_e_observability"]["object_has_obb"] = 1
    elif control_type == "missing_mesh_control":
        base["Q_e_safe"]["mesh_or_point_availability"] = "missing_mesh"
        base["Q_e_observability"]["subject_has_obb"] = 1
        base["Q_e_observability"]["object_has_obb"] = 1
    elif control_type == "shuffled_view_control":
        base["geometry_observable"] = True
        base["mesh_or_semseg_available"] = True
        base["object_obb_available"] = True
        base["Q_e_safe"]["raw_geometry_available"] = True
        base["Q_e_safe"]["object_pair_feature_coverage"] = 0.5
        base["Q_e_safe"]["raw_geometry_feature_count"] = 8
        base["Q_e_safe"]["mesh_or_point_availability"] = "shuffled_view"
        base["Q_e_observability"]["q_e_state_code"] = 0.1
        base["Q_e_observability"]["q_e_state_limited"] = 1
        base["Q_e_observability"]["q_e_state_uncertain"] = 0
        base["Q_e_observability"]["subject_has_obb"] = 1
        base["Q_e_observability"]["object_has_obb"] = 1
        base["Q_e_observability"]["view_pair_mismatch_flag"] = 1
    return base


def target_y(row: dict[str, Any]) -> int:
    if "target_y" in row:
        return int(row["target_y"])
    labels = row.get("labels", {})
    if isinstance(labels, dict) and "C_e" in labels:
        return int(labels["C_e"])
    raise KeyError("missing target_y/C_e label")


def decision_label(obs_label: int, rel_label: int | None) -> str:
    if obs_label == 0:
        return "abstain"
    return "accept" if int(rel_label or 0) == 1 else "reject"


def build_views_for_row(row: dict[str, Any], eval_split: str, control_type: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    identity = base_identity(row, eval_split)
    if control_type != "observed_original":
        identity["candidate_id"] = f"{identity['source_candidate_id']}::pobs_control::{control_type}"
        identity["control_type"] = control_type
        identity["row_role"] = "synthetic_unobservable_control"
        q = control_q(control_type)
        obs = 0
        rel = None
    else:
        q = original_q(q_block(row))
        obs = 1
        rel = target_y(row)

    qe_view = {
        **identity,
        "schema_version": f"{SCHEMA_VERSION}_qe_view",
        "feature_blocks": {"Q_e": q},
        "feature_use_policy": {
            "allowed_blocks": ["Q_e"],
            "blocked_blocks": ["T_e", "G_e", "Z_e", "hidden_selective_labels"],
        },
    }
    prel_view = {
        **identity,
        "schema_version": f"{SCHEMA_VERSION}_prel_view",
        "feature_blocks": {
            "T_e": t_block(row),
            "G_e": g_block(row),
            "Q_e": q,
            "Z_e": z_block(row),
        },
        "feature_use_policy": {
            "allowed_blocks": ["T_e", "G_e", "Q_e", "Z_e"],
            "blocked_fields": ["obs_label", "rel_label", "decision_label", "target_y", "gt_match", "p_geom_valid"],
        },
    }
    hidden = {
        **identity,
        "schema_version": f"{SCHEMA_VERSION}_hidden_labels",
        "label_only": True,
        "obs_label": obs,
        "rel_label": rel,
        "decision_label": decision_label(obs, rel),
        "target_policy": "observed rows use C_e/target_y; missing-evidence controls force abstain",
    }
    return qe_view, prel_view, hidden


def load_rows(internal_split_dir: Path, official_materialization_dir: Path) -> list[tuple[dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], str]] = []
    for row in iter_jsonl(internal_split_dir / "model_safe_split_view.jsonl"):
        split = str(row.get("protocol_split") or row.get("split") or "internal_unknown")
        rows.append((row, split))
    for row in iter_jsonl(official_materialization_dir / "model_safe_view.jsonl"):
        rows.append((row, "official_validation"))
    return rows


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    protocol_dir = args.protocol_dir if args.protocol_dir.is_absolute() else repo_root / args.protocol_dir
    internal_split_dir = args.internal_split_dir if args.internal_split_dir.is_absolute() else repo_root / args.internal_split_dir
    official_dir = args.official_materialization_dir if args.official_materialization_dir.is_absolute() else repo_root / args.official_materialization_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    summary = read_json(protocol_dir / "summary.json")
    if summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error": "unexpected_protocol_status", "observed": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error": "unexpected_protocol_next", "observed": summary.get("next_todo")})

    all_inputs = load_rows(internal_split_dir, official_dir)
    qe_rows: list[dict[str, Any]] = []
    prel_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for row, eval_split in all_inputs:
        for control_type in ["observed_original", *CONTROL_TYPES]:
            qe, prel, hidden = build_views_for_row(row, eval_split, control_type)
            qe_rows.append(qe)
            prel_rows.append(prel)
            hidden_rows.append(hidden)

    write_jsonl(out / "validation_errors.jsonl", errors)
    write_jsonl(out / "model_safe_qe_view.jsonl", qe_rows)
    write_jsonl(out / "model_safe_prel_view.jsonl", prel_rows)
    write_jsonl(out / "hidden_selective_labels.jsonl", hidden_rows)

    split_counts = Counter(row["eval_split"] for row in hidden_rows)
    role_counts = Counter(row["row_role"] for row in hidden_rows)
    decision_counts = Counter(row["decision_label"] for row in hidden_rows)
    obs_counts = Counter(str(row["obs_label"]) for row in hidden_rows)
    rel_counts = Counter(str(row["rel_label"]) for row in hidden_rows if row["rel_label"] is not None)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_dir": rel_path(repo_root, protocol_dir),
        "internal_split_dir": rel_path(repo_root, internal_split_dir),
        "official_materialization_dir": rel_path(repo_root, official_dir),
        "outputs": {
            "model_safe_qe_view": rel_path(repo_root, out / "model_safe_qe_view.jsonl"),
            "model_safe_prel_view": rel_path(repo_root, out / "model_safe_prel_view.jsonl"),
            "hidden_selective_labels": rel_path(repo_root, out / "hidden_selective_labels.jsonl"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "row_counts": {
            "input_observed_rows": len(all_inputs),
            "output_rows_per_view": len(hidden_rows),
            "missing_control_types": CONTROL_TYPES,
            "split_counts": dict(sorted(split_counts.items())),
            "role_counts": dict(sorted(role_counts.items())),
            "obs_counts": dict(sorted(obs_counts.items())),
            "rel_counts_observed_only": dict(sorted(rel_counts.items())),
            "decision_counts": dict(sorted(decision_counts.items())),
        },
        "claim_boundary": {
            "pobs_prel_main_framework_claim_allowed": True,
            "pobs_prel_quantitative_result_claim_allowed": False,
            "synthetic_missing_evidence_controls_used": True,
            "independent_human_observability_labels_used": False,
            "official_test_used": False,
        },
        "next_todo": "compatibility_dataset_v3_pobs_prel_schema_audit_after_materialization",
        "validation_errors": len(errors),
    }
    write_json(out / "materialization_manifest.json", manifest)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
