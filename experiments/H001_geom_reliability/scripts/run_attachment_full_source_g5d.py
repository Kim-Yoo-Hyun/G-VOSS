#!/usr/bin/env python3
"""Run attachment-deferred G5d full-source scoring, metrics, and controls.

This promotes the frozen G5c protocol to source-result evidence, but it still
does not update the current AAAI main claim. Main-claim promotion requires an
explicit user decision after reviewing the outputs.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np

from fit_attachment_strict_calibration import evidence_features
from run_attachment_deferred_extractor_dry_run import (
    PREDICATE_LABELS,
    TARGET_FAMILY,
    ensure_dir,
    iter_jsonl,
    read_json,
    relpath,
    row_edge,
    row_family,
    row_label,
    utc_now,
    write_json,
    write_jsonl,
)
from run_attachment_gt_policy_smoke import (
    build_point_surface_evidence,
    decision_row,
    policy_thresholds,
)
from run_attachment_source_scoring_preflight import (
    finite_float,
    normalize_source_row,
    quantiles,
    row_id_for_source,
    score_evidence_row,
)
from validate_attachment_deferred_point_surface import (
    DEFAULT_CONTACT_THRESHOLD_M,
    DEFAULT_MAX_POINTS_PER_OBJECT,
)


SCHEMA_VERSION = "h001_attachment_deferred_g5d_full_source_v1"
SCORED_ROW_SCHEMA_VERSION = "h001_attachment_deferred_source_p_geom_score_v1"
STATUS = "attachment_deferred_g5d_full_source_metrics_ready"
TARGET_LABELS = tuple(PREDICATE_LABELS)
DEFAULT_ROOT = Path("experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_PROTOCOL_DIR = DEFAULT_ROOT / "full_source_protocol"
DEFAULT_CALIBRATION_DIR = DEFAULT_ROOT / "calibration_fit"
DEFAULT_POLICY_DIR = DEFAULT_ROOT / "verifier_policy"
DEFAULT_OUT = DEFAULT_ROOT / "full_source_g5d"
DEFAULT_GT = Path(
    "hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
)
DEFAULT_VLSAT = Path(
    "hypothesis/CAND-001/H001_geometry-grounded-verification/"
    "artifacts/evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl"
)
DEFAULT_OPEN3DSG = Path("experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl")
KS = (50, 100)
CONDITIONS = (
    "semantic_only",
    "probabilistic_recalibrated",
    "rule_verified_attachment_policy",
    "control_p_geom_valid_only",
    "control_distance_only",
    "control_shuffled_geometry",
    "control_wrong_pair_geometry",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--policy-dir", type=Path, default=DEFAULT_POLICY_DIR)
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GT)
    parser.add_argument("--vlsat-verification", type=Path, default=DEFAULT_VLSAT)
    parser.add_argument("--open3dsg-verification", type=Path, default=DEFAULT_OPEN3DSG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--contact-threshold-m", type=float, default=DEFAULT_CONTACT_THRESHOLD_M)
    parser.add_argument("--max-points-per-object", type=int, default=DEFAULT_MAX_POINTS_PER_OBJECT)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260606)
    parser.add_argument("--limit-shards", type=int, default=0)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(iter_jsonl(path))


def exact_key_from_parts(row: dict[str, Any]) -> tuple[str, str, int, int, str]:
    return (
        str(row["scan_id"]),
        str(row["subgraph_id"]),
        int(row["subject_id"]),
        int(row["object_id"]),
        str(row["predicate_label"]),
    )


def gt_key(row: dict[str, Any]) -> tuple[str, str, int, int, str]:
    return exact_key_from_parts(row)


def pair_key(row: dict[str, Any]) -> tuple[int, int]:
    return int(row["subject_id"]), int(row["object_id"])


def source_score(row: dict[str, Any]) -> float:
    semantic = row.get("semantic") if isinstance(row.get("semantic"), dict) else {}
    score = finite_float(semantic.get("ranking_score"))
    if score is None:
        score = finite_float(semantic.get("predicate_score"))
    return float(score) if score is not None else 0.0


def distance_score(row: dict[str, Any]) -> float | None:
    snapshot = row.get("feature_snapshot") if isinstance(row.get("feature_snapshot"), dict) else {}
    distance = finite_float(snapshot.get("min_point_distance_m"))
    if distance is None:
        distance = finite_float(snapshot.get("surface_distance_m"))
    if distance is None:
        return None
    return 1.0 / (1.0 + max(distance, 0.0))


def geometry_missing(row: dict[str, Any]) -> bool:
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    available = evidence.get("geometry_available") if isinstance(evidence.get("geometry_available"), dict) else {}
    return not (
        available.get("points")
        and available.get("surface_candidates")
        and available.get("normals")
    )


def load_source_rows(
    *,
    path: Path,
    source_name: str,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    by_label: dict[str, list[dict[str, Any]]] = {label: [] for label in TARGET_LABELS}
    rows_read = 0
    attachment_rows = 0
    skipped = Counter()
    for row in iter_jsonl(path):
        rows_read += 1
        if row_family(row) != TARGET_FAMILY:
            continue
        attachment_rows += 1
        label = row_label(row)
        if label not in by_label:
            skipped["label_out_of_scope"] += 1
            continue
        normalized = normalize_source_row(row, source_name)
        if normalized is None:
            skipped["normalization_failed"] += 1
            continue
        normalized["source_label_ordinal"] = len(by_label[label])
        normalized["source_global_ordinal"] = attachment_rows - 1
        by_label[label].append(normalized)
    return by_label, {
        "path": str(path),
        "source_name": source_name,
        "rows_read": rows_read,
        "attachment_rows": attachment_rows,
        "by_label": {label: len(rows) for label, rows in by_label.items()},
        "skipped": dict(sorted(skipped.items())),
    }


def validate_scored_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if row.get("schema_version") != SCORED_ROW_SCHEMA_VERSION:
        errors.append("bad_schema_version")
    if row.get("predicate_family") != TARGET_FAMILY:
        errors.append("bad_predicate_family")
    if row.get("predicate_label") not in TARGET_LABELS:
        errors.append("bad_predicate_label")
    if row.get("attachment_policy_decision") not in {"satisfied", "violated", "uncertain"}:
        errors.append("bad_attachment_policy_decision")
    p_geom_valid = finite_float(row.get("p_geom_valid"))
    if p_geom_valid is None or not (0.0 <= p_geom_valid <= 1.0):
        errors.append("bad_p_geom_valid")
    semantic = row.get("semantic") if isinstance(row.get("semantic"), dict) else {}
    if finite_float(semantic.get("ranking_score")) is None and finite_float(semantic.get("predicate_score")) is None:
        errors.append("missing_semantic_score")
    for forbidden in ("recall_credit", "gt_match", "ranked_at_k", "metric_condition", "violation_at_k"):
        if forbidden in row:
            errors.append(f"forbidden_field:{forbidden}")
    return errors


def score_shard(
    *,
    shard: dict[str, Any],
    rows: list[dict[str, Any]],
    dataset_root: Path,
    model: dict[str, Any],
    thresholds: dict[str, float],
    out: Path,
    contact_threshold_m: float,
    max_points_per_object: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    shard_dir = out / "shards" / shard["shard_id"]
    ensure_dir(shard_dir)
    evidence_rows, diagnostics, evidence_meta = build_point_surface_evidence(
        source_rows=rows,
        dataset_root=dataset_root,
        contact_threshold_m=contact_threshold_m,
        max_points_per_object=max_points_per_object,
    )
    source_by_row_id = {row_id_for_source(row): row for row in rows}
    scored_rows: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    unknown_categories = Counter()
    decision_counts = Counter()
    for evidence in evidence_rows:
        source_meta = source_by_row_id.get(evidence["row_id"], {})
        probability, features, unknowns = score_evidence_row(evidence, model=model)
        for unknown in unknowns:
            unknown_categories[unknown] += 1
        decision = decision_row(evidence, thresholds)
        decision_counts[decision["verification_status"]] += 1
        semantic_score = source_meta.get("semantic_score")
        ranking_score = source_meta.get("ranking_score")
        row = {
            "schema_version": SCORED_ROW_SCHEMA_VERSION,
            "record_type": "attachment_deferred_source_p_geom_score",
            "score_scope": "full_source_g5d",
            "calibration_model_id": model["model_id"],
            "source_name": evidence["source_name"],
            "source_prediction_id": source_meta.get("source_prediction_id"),
            "baseline_run_id": source_meta.get("baseline_run_id"),
            "scan_id": evidence["scan_id"],
            "subgraph_id": evidence["subgraph_id"],
            "subject_id": int(evidence["subject_id"]),
            "object_id": int(evidence["object_id"]),
            "subject_label": evidence.get("subject_label"),
            "object_label": evidence.get("object_label"),
            "predicate_family": evidence["predicate_family"],
            "predicate_label": evidence["predicate_label"],
            "subtype_hint": evidence.get("subtype_hint"),
            "source_label_ordinal": source_meta.get("source_label_ordinal"),
            "source_global_ordinal": source_meta.get("source_global_ordinal"),
            "semantic": {
                "predicate_score": semantic_score,
                "ranking_score": ranking_score,
                "semantic_rank_in_subgraph": source_meta.get("semantic_rank_in_subgraph"),
                "predicate_rank_for_pair": source_meta.get("predicate_rank_for_pair"),
            },
            "evidence": {
                "row_id": evidence["row_id"],
                "extractor_status": evidence.get("extractor_status"),
                "geometry_available": evidence.get("geometry_available"),
                "missing_fields": evidence.get("missing_fields", []),
                "quality_flags": evidence.get("quality_flags", []),
                "unknown_model_categories": unknowns,
            },
            "attachment_policy_name": decision["policy_name"],
            "attachment_policy_decision": decision["verification_status"],
            "attachment_policy_reason_codes": decision["reason_codes"],
            "attachment_policy_uncertain_by_design": decision["uncertain_by_design"],
            "p_geom_valid": probability,
            "p_geom_invalid": 1.0 - probability,
            "feature_snapshot": {
                key: features.get(key)
                for key in (
                    "min_point_distance_m",
                    "contact_patch_score",
                    "surface_candidate_count",
                    "surface_distance_m",
                    "surface_projected_overlap_ratio",
                    "distance_3d_m",
                    "distance_xy_m",
                    "normalized_distance_3d",
                    "normalized_distance_xy",
                    "center_delta_z_m",
                    "vertical_gap_m",
                    "projected_xy_overlap",
                    "floor_clearance_m",
                    "hanging_geometry_score",
                    "support_explanation_score",
                    "surface_type",
                    "surface_normal_class",
                    "class_pair_prior",
                )
            },
        }
        errors = validate_scored_row(row)
        if errors:
            validation_errors.append({"row_id": evidence["row_id"], "errors": errors})
        scored_rows.append(row)

    status = "complete" if not validation_errors and len(scored_rows) == int(shard["expected_rows"]) else "failed"
    status_payload = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": utc_now(),
        "shard": shard,
        "counts": {
            "source_rows": len(rows),
            "evidence_rows": len(evidence_rows),
            "diagnostics": len(diagnostics),
            "scored_rows": len(scored_rows),
            "validation_errors": len(validation_errors),
            "decision_counts": dict(sorted(decision_counts.items())),
            "unknown_model_category_counts": dict(sorted(unknown_categories.items())),
        },
        "evidence_meta": evidence_meta,
    }
    write_jsonl(shard_dir / "source_rows.jsonl", rows)
    write_jsonl(shard_dir / "evidence_rows.jsonl", evidence_rows)
    write_jsonl(shard_dir / "diagnostics.jsonl", diagnostics)
    write_jsonl(shard_dir / "scored_rows.jsonl", scored_rows)
    write_json(shard_dir / "status.json", status_payload)
    return scored_rows, status_payload, validation_errors


def donor_map_shuffled(rows: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["source_name"], row["predicate_label"])].append(row)
    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: (row["scan_id"], row["subgraph_id"], row["subject_id"], row["object_id"], row["predicate_label"]))
        if len(group_rows) < 2:
            continue
        shift = max(1, len(group_rows) // 2)
        for index, row in enumerate(group_rows):
            donor = group_rows[(index + shift) % len(group_rows)]
            result[str(row["source_prediction_id"])] = float(donor["p_geom_valid"])
    return result


def donor_map_wrong_pair(rows: list[dict[str, Any]], fallback: dict[str, float]) -> dict[str, float]:
    result: dict[str, float] = {}
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["source_name"], row["subgraph_id"], row["predicate_label"])].append(row)
    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: (pair_key(row), row["predicate_label"], str(row["source_prediction_id"])))
        if len({pair_key(row) for row in group_rows}) < 2:
            continue
        for index, row in enumerate(group_rows):
            for offset in range(1, len(group_rows)):
                donor = group_rows[(index + offset) % len(group_rows)]
                if pair_key(donor) != pair_key(row):
                    result[str(row["source_prediction_id"])] = float(donor["p_geom_valid"])
                    break
    for key, value in fallback.items():
        result.setdefault(key, value)
    return result


def condition_scores(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | None]]:
    shuffled = donor_map_shuffled(rows)
    wrong_pair = donor_map_wrong_pair(rows, shuffled)
    scores: dict[str, dict[str, float | None]] = {condition: {} for condition in CONDITIONS}
    for row in rows:
        pid = str(row["source_prediction_id"])
        semantic = source_score(row)
        p_geom = finite_float(row.get("p_geom_valid"))
        scores["semantic_only"][pid] = semantic
        scores["probabilistic_recalibrated"][pid] = semantic * p_geom if p_geom is not None else None
        scores["rule_verified_attachment_policy"][pid] = (
            semantic if row["attachment_policy_decision"] != "violated" else -1.0
        )
        scores["control_p_geom_valid_only"][pid] = p_geom
        scores["control_distance_only"][pid] = distance_score(row)
        donor = shuffled.get(pid)
        scores["control_shuffled_geometry"][pid] = semantic * donor if donor is not None else None
        donor_wrong = wrong_pair.get(pid)
        scores["control_wrong_pair_geometry"][pid] = semantic * donor_wrong if donor_wrong is not None else None
    return scores


def select_topk_by_subgraph(
    rows: list[dict[str, Any]],
    scores: dict[str, float | None],
    k: int,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["subgraph_id"])].append(row)
    selected: dict[str, list[dict[str, Any]]] = {}
    for subgraph_id, group_rows in grouped.items():
        selected[subgraph_id] = sorted(
            group_rows,
            key=lambda row: (
                -(scores.get(str(row["source_prediction_id"])) if scores.get(str(row["source_prediction_id"])) is not None else -math.inf),
                int(row["subject_id"]),
                int(row["object_id"]),
                row["predicate_label"],
                str(row["source_prediction_id"]),
            ),
        )[:k]
    return selected


def source_metrics(
    *,
    rows: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    denominator_audit: dict[str, Any],
    n_bootstrap: int,
    seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = np.random.default_rng(seed)
    gt_all = [row for row in ground_truth if row.get("predicate_label") in TARGET_LABELS]
    gt_keys_all = {gt_key(row) for row in gt_all}
    metrics: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "created_at": utc_now(),
        "family": TARGET_FAMILY,
        "labels": list(TARGET_LABELS),
        "ks": list(KS),
        "conditions": {},
        "counts": {},
        "warnings": [],
    }
    bootstrap: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "created_at": metrics["created_at"],
        "n_bootstrap": n_bootstrap,
        "seed": seed,
        "sources": {},
    }
    for source_name in sorted({row["source_name"] for row in rows}):
        source_rows = [row for row in rows if row["source_name"] == source_name]
        source_exact_keys = {exact_key_from_parts(row) for row in source_rows}
        covered_gt = [row for row in gt_all if gt_key(row) in source_exact_keys]
        covered_gt_keys = {gt_key(row) for row in covered_gt}
        audit_source = denominator_audit.get("sources", {}).get(source_name, {})
        if audit_source and int(audit_source.get("covered_exact_label_gt_denominator", -1)) != len(covered_gt_keys):
            metrics["warnings"].append(
                f"{source_name}:covered_gt_denominator_mismatch:"
                f"computed={len(covered_gt_keys)} audit={audit_source.get('covered_exact_label_gt_denominator')}"
            )
        gt_by_subgraph: dict[str, set[tuple[str, str, int, int, str]]] = defaultdict(set)
        for row in covered_gt:
            gt_by_subgraph[str(row["subgraph_id"])].add(gt_key(row))
        subgraph_ids = sorted(set(gt_by_subgraph) | {str(row["subgraph_id"]) for row in source_rows})
        score_maps = condition_scores(source_rows)
        source_block: dict[str, Any] = {
            "source_name": source_name,
            "covered_exact_label_gt_denominator": len(covered_gt_keys),
            "global_exact_label_gt_denominator": len(gt_keys_all),
            "coverage_ratio_vs_global": len(covered_gt_keys) / len(gt_keys_all) if gt_keys_all else None,
            "missing_exact_label_gt_rows": len(gt_keys_all - covered_gt_keys),
            "rows": len(source_rows),
            "subgraphs": len({row["subgraph_id"] for row in source_rows}),
            "conditions": {},
        }
        boot_source = {"conditions": {}}
        for condition in CONDITIONS:
            condition_block: dict[str, Any] = {
                "score_summary": {
                    "missing_scores": sum(1 for row in source_rows if score_maps[condition].get(str(row["source_prediction_id"])) is None),
                    "values": quantiles(
                        [
                            float(score)
                            for score in score_maps[condition].values()
                            if score is not None and math.isfinite(float(score))
                        ]
                    ),
                },
                "recall": {"denominator": len(covered_gt_keys), "by_k": {}, "by_predicate_label": {}},
                "violation_rate": {"by_k": {}},
            }
            boot_condition: dict[str, Any] = {}
            for k in KS:
                selected_by_sg = select_topk_by_subgraph(source_rows, score_maps[condition], k)
                selected = [row for group in selected_by_sg.values() for row in group]
                selected_keys = {exact_key_from_parts(row) for row in selected}
                correct = len(selected_keys & covered_gt_keys)
                violated = sum(1 for row in selected if row["attachment_policy_decision"] == "violated")
                uncertain = sum(1 for row in selected if row["attachment_policy_decision"] == "uncertain")
                missing_evidence = sum(1 for row in selected if geometry_missing(row))
                condition_block["recall"]["by_k"][str(k)] = {
                    "correct": correct,
                    "denominator": len(covered_gt_keys),
                    "recall": correct / len(covered_gt_keys) if covered_gt_keys else None,
                    "selected_predictions": len(selected),
                }
                condition_block["violation_rate"]["by_k"][str(k)] = {
                    "violated": violated,
                    "uncertain": uncertain,
                    "evidence_missing": missing_evidence,
                    "denominator": len(selected),
                    "violation_rate": violated / len(selected) if selected else None,
                    "uncertain_rate": uncertain / len(selected) if selected else None,
                    "evidence_missing_rate": missing_evidence / len(selected) if selected else None,
                }
                per_label = {}
                for label in TARGET_LABELS:
                    label_gt_keys = {gt_key(row) for row in covered_gt if row["predicate_label"] == label}
                    label_selected_keys = {exact_key_from_parts(row) for row in selected if row["predicate_label"] == label}
                    label_correct = len(label_selected_keys & label_gt_keys)
                    per_label[label] = {
                        "correct": label_correct,
                        "denominator": len(label_gt_keys),
                        "recall": label_correct / len(label_gt_keys) if label_gt_keys else None,
                    }
                condition_block["recall"]["by_predicate_label"][str(k)] = per_label
                per_sg = []
                for subgraph_id in subgraph_ids:
                    sg_selected = selected_by_sg.get(subgraph_id, [])
                    sg_selected_keys = {exact_key_from_parts(row) for row in sg_selected}
                    sg_gt = gt_by_subgraph.get(subgraph_id, set())
                    per_sg.append(
                        (
                            len(sg_selected_keys & sg_gt),
                            len(sg_gt),
                            sum(1 for row in sg_selected if row["attachment_policy_decision"] == "violated"),
                            len(sg_selected),
                        )
                    )
                boot_condition[str(k)] = bootstrap_ci(per_sg, rng, n_bootstrap)
            source_block["conditions"][condition] = condition_block
            boot_source["conditions"][condition] = boot_condition
        metrics["conditions"][source_name] = source_block
        bootstrap["sources"][source_name] = boot_source
        metrics["counts"][source_name] = {
            "source_rows": len(source_rows),
            "covered_gt": len(covered_gt_keys),
            "global_gt": len(gt_keys_all),
            "label_counts": dict(sorted(Counter(row["predicate_label"] for row in source_rows).items())),
            "decision_counts": dict(sorted(Counter(row["attachment_policy_decision"] for row in source_rows).items())),
        }
    return metrics, bootstrap


def bootstrap_ci(
    per_subgraph: list[tuple[int, int, int, int]],
    rng: np.random.Generator,
    n_bootstrap: int,
) -> dict[str, Any]:
    if not per_subgraph or n_bootstrap <= 0:
        return {"recall": None, "violation_rate": None}
    data = np.asarray(per_subgraph, dtype=np.float64)
    n = data.shape[0]
    recall_values = np.empty(n_bootstrap, dtype=np.float64)
    violation_values = np.empty(n_bootstrap, dtype=np.float64)
    for idx in range(n_bootstrap):
        sample = data[rng.integers(0, n, size=n)]
        recall_den = sample[:, 1].sum()
        violation_den = sample[:, 3].sum()
        recall_values[idx] = sample[:, 0].sum() / recall_den if recall_den > 0 else np.nan
        violation_values[idx] = sample[:, 2].sum() / violation_den if violation_den > 0 else np.nan
    return {
        "recall": percentile(recall_values),
        "violation_rate": percentile(violation_values),
    }


def percentile(values: np.ndarray) -> dict[str, Any]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {"median": None, "ci95": [None, None], "valid_samples": 0}
    lo, med, hi = np.percentile(finite, [2.5, 50.0, 97.5])
    return {"median": float(med), "ci95": [float(lo), float(hi)], "valid_samples": int(finite.size)}


def failure_rows(scored_rows: list[dict[str, Any]], metrics: dict[str, Any], limit: int = 300) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for source_name in sorted(metrics["conditions"]):
        source_rows = [row for row in scored_rows if row["source_name"] == source_name]
        scores = condition_scores(source_rows)["semantic_only"]
        selected = select_topk_by_subgraph(source_rows, scores, 100)
        for row in [item for rows in selected.values() for item in rows]:
            if row["attachment_policy_decision"] != "violated":
                continue
            failures.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "source_name": source_name,
                    "condition": "semantic_only",
                    "scan_id": row["scan_id"],
                    "subgraph_id": row["subgraph_id"],
                    "subject_id": row["subject_id"],
                    "object_id": row["object_id"],
                    "predicate_label": row["predicate_label"],
                    "semantic_score": source_score(row),
                    "p_geom_valid": row["p_geom_valid"],
                    "attachment_policy_decision": row["attachment_policy_decision"],
                    "attachment_policy_reason_codes": row["attachment_policy_reason_codes"],
                    "feature_snapshot": row["feature_snapshot"],
                }
            )
    failures.sort(key=lambda row: (row["source_name"], -float(row["semantic_score"]), row["scan_id"]))
    return failures[:limit]


def commands_md() -> str:
    return """# Attachment Deferred G5d Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \\
  attachment_deferred_full_source_g5d
```

This runs full-source attachment-deferred scoring, source metrics, controls,
and subgraph bootstrap CI under the frozen G5c protocol. It does not promote
`attachment_deferred` to the AAAI main claim.
"""


def report_md(manifest: dict[str, Any], metrics: dict[str, Any]) -> str:
    lines = [
        "# Attachment Deferred G5d Full-Source Metrics",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "`attachment_deferred` remains outside the current AAAI main claim unless",
        "explicitly promoted after reviewing this artifact. This G5d run provides",
        "source metrics and controls, not a paper-claim update by itself.",
        "",
        "## Counts",
        "",
        f"- scored rows: `{manifest['counts']['scored_rows']}`",
        f"- validation errors: `{manifest['counts']['validation_errors']}`",
        f"- shards complete: `{manifest['counts']['complete_shards']}` / `{manifest['counts']['shards']}`",
        "",
        "## Source Metrics",
        "",
    ]
    for source_name, source_block in metrics["conditions"].items():
        lines.extend(
            [
                f"### {source_name}",
                "",
                f"- covered denominator: `{source_block['covered_exact_label_gt_denominator']}` / `{source_block['global_exact_label_gt_denominator']}`",
                f"- missing exact-label GT rows: `{source_block['missing_exact_label_gt_rows']}`",
                "",
                "| condition | R@50 | R@100 | V@50 | V@100 | U@100 |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for condition in CONDITIONS:
            cond = source_block["conditions"][condition]
            r50 = cond["recall"]["by_k"]["50"]["recall"]
            r100 = cond["recall"]["by_k"]["100"]["recall"]
            v50 = cond["violation_rate"]["by_k"]["50"]["violation_rate"]
            v100 = cond["violation_rate"]["by_k"]["100"]["violation_rate"]
            u100 = cond["violation_rate"]["by_k"]["100"]["uncertain_rate"]
            lines.append(
                f"| `{condition}` | {fmt(r50)} | {fmt(r100)} | {fmt(v50)} | {fmt(v100)} | {fmt(u100)} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Warnings",
            "",
        ]
    )
    if manifest["warnings"]:
        lines.extend(f"- `{warning}`" for warning in manifest["warnings"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = resolve(repo_root, args.dataset_root)
    protocol_dir = resolve(repo_root, args.protocol_dir)
    calibration_dir = resolve(repo_root, args.calibration_dir)
    policy_dir = resolve(repo_root, args.policy_dir)
    ground_truth_path = resolve(repo_root, args.ground_truth)
    vlsat_path = resolve(repo_root, args.vlsat_verification)
    open3dsg_path = resolve(repo_root, args.open3dsg_verification)
    out = resolve(repo_root, args.out)

    protocol = read_json(protocol_dir / "protocol.json")
    denominator_audit = read_json(protocol_dir / "denominator_audit.json")
    protocol_manifest = read_json(protocol_dir / "manifest.json")
    model = read_json(calibration_dir / "model.json")
    policy = read_json(policy_dir / "verifier_policy.json")
    thresholds = policy_thresholds(policy)
    shards = load_jsonl(protocol_dir / "shards.jsonl")
    if args.limit_shards > 0:
        shards = shards[: args.limit_shards]
    if protocol_manifest.get("status") != "attachment_deferred_full_source_protocol_frozen_no_metrics":
        raise ValueError(f"unexpected_protocol_status:{protocol_manifest.get('status')}")
    if model.get("status") != "attachment_deferred_calibration_fit_ready_no_source_metrics":
        raise ValueError(f"unexpected_model_status:{model.get('status')}")

    source_rows_by_source_label: dict[tuple[str, str], list[dict[str, Any]]] = {}
    source_load_summary: dict[str, Any] = {}
    for source_key, source_name, path in (
        ("vlsat", "vlsat_closed_set", vlsat_path),
        ("open3dsg", "open3dsg_ov", open3dsg_path),
    ):
        by_label, summary = load_source_rows(path=path, source_name=source_name)
        source_load_summary[source_name] = summary
        for label, rows in by_label.items():
            source_rows_by_source_label[(source_key, label)] = rows

    scored_rows: list[dict[str, Any]] = []
    shard_statuses: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    for shard in shards:
        rows = source_rows_by_source_label[(shard["source_key"], shard["predicate_label"])][
            int(shard["start_ordinal_in_source_label"]) : int(shard["end_ordinal_exclusive"])
        ]
        shard_scored, shard_status, shard_errors = score_shard(
            shard=shard,
            rows=rows,
            dataset_root=dataset_root,
            model=model,
            thresholds=thresholds,
            out=out,
            contact_threshold_m=args.contact_threshold_m,
            max_points_per_object=args.max_points_per_object,
        )
        scored_rows.extend(shard_scored)
        shard_statuses.append(shard_status)
        validation_errors.extend({"shard_id": shard["shard_id"], **error} for error in shard_errors)

    metrics, bootstrap = source_metrics(
        rows=scored_rows,
        ground_truth=load_jsonl(ground_truth_path),
        denominator_audit=denominator_audit,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
    )
    failures = failure_rows(scored_rows, metrics)
    status = STATUS if not validation_errors and all(item["status"] == "complete" for item in shard_statuses) else "attachment_deferred_g5d_full_source_metrics_failed_validation"
    warnings = list(metrics.get("warnings", []))
    if args.limit_shards > 0:
        warnings.append(f"limit_shards_active:{args.limit_shards}")
    if "connected_to_dev_absent_use_pooled_or_train_only_caveat" not in warnings:
        warnings.append("connected_to_dev_absent_use_pooled_or_train_only_caveat")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": utc_now(),
        "claim_boundary": {
            "artifact_type": "attachment_deferred_full_source_source_metrics",
            "current_main_AAAI_claim_unchanged": True,
            "attachment_promotion_requires_user_confirmation": True,
            "promoted_to_main_claim": False,
        },
        "inputs": {
            "protocol": relpath(repo_root, protocol_dir / "protocol.json"),
            "denominator_audit": relpath(repo_root, protocol_dir / "denominator_audit.json"),
            "calibration_model": relpath(repo_root, calibration_dir / "model.json"),
            "verifier_policy": relpath(repo_root, policy_dir / "verifier_policy.json"),
            "ground_truth": relpath(repo_root, ground_truth_path),
            "vlsat_verification": relpath(repo_root, vlsat_path),
            "open3dsg_verification": relpath(repo_root, open3dsg_path),
            "dataset_root": relpath(repo_root, dataset_root),
        },
        "outputs": {
            "manifest": "manifest.json",
            "summary": "summary.json",
            "scored_rows": "scored_rows.jsonl",
            "metrics": "metrics.json",
            "bootstrap_ci": "bootstrap_ci.json",
            "failure_rows": "failure_rows.jsonl",
            "validation": "validation.json",
            "commands": "commands.md",
            "report": "report.md",
            "shards": "shards/<shard_id>/",
        },
        "counts": {
            "shards": len(shard_statuses),
            "complete_shards": sum(1 for item in shard_statuses if item["status"] == "complete"),
            "scored_rows": len(scored_rows),
            "validation_errors": len(validation_errors),
            "failure_rows": len(failures),
            "expected_total_source_rows": protocol.get("full_source_scoring", {}).get("expected_total_source_rows"),
        },
        "source_load_summary": source_load_summary,
        "warnings": warnings,
        "blockers": [
            "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
            "qualitative_or_visual_audit_still_required_before_main_claim_promotion",
        ],
        "next_gate": "G5e_attachment_failure_visual_audit_if_promotion_is_considered",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": manifest["created_at"],
        "counts": manifest["counts"],
        "metrics_digest": {
            source: {
                condition: {
                    "r100": block["conditions"][condition]["recall"]["by_k"]["100"]["recall"],
                    "violation100": block["conditions"][condition]["violation_rate"]["by_k"]["100"]["violation_rate"],
                    "uncertain100": block["conditions"][condition]["violation_rate"]["by_k"]["100"]["uncertain_rate"],
                }
                for condition in CONDITIONS
            }
            for source, block in metrics["conditions"].items()
        },
        "warnings": warnings,
    }
    validation = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if not validation_errors else "failed",
        "validation_errors": validation_errors[:1000],
        "validation_error_count": len(validation_errors),
        "shard_status_counts": dict(sorted(Counter(item["status"] for item in shard_statuses).items())),
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_jsonl(out / "scored_rows.jsonl", scored_rows)
    write_json(out / "metrics.json", metrics)
    write_json(out / "bootstrap_ci.json", bootstrap)
    write_jsonl(out / "failure_rows.jsonl", failures)
    write_json(out / "validation.json", validation)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, metrics))
    print(
        json.dumps(
            {
                "status": status,
                "out": relpath(repo_root, out),
                "scored_rows": len(scored_rows),
                "validation_errors": len(validation_errors),
                "complete_shards": manifest["counts"]["complete_shards"],
                "shards": manifest["counts"]["shards"],
                "warnings": warnings,
            },
            sort_keys=True,
        )
    )
    return 0 if status == STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
