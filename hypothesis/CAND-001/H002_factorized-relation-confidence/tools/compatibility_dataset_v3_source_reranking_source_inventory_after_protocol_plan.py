#!/usr/bin/env python3
"""Inventory source candidates for H002 source reranking after protocol lock."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock"
)
DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan"
)
DEFAULT_H2_OFFICIAL_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_materialization/latest"
DEFAULT_H2_OFFICIAL_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_evaluation/latest"
DEFAULT_VALIDATION_GT = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_validation.json"
DEFAULT_OUTPUT_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan"
)

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan_input_errors"
SELECTED_PATH = "source_inventory_ready_select_source_candidate_materialization_protocol"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory"

PREDICATE_TO_FAMILY = {
    "higher than": "relative_vertical",
    "lower than": "relative_vertical",
    "bigger than": "size_relative",
    "smaller than": "size_relative",
    "left": "relative_horizontal",
    "right": "relative_horizontal",
    "front": "relative_horizontal",
    "behind": "relative_horizontal",
    "close by": "proximity",
    "standing on": "support_contact",
    "lying on": "support_contact",
    "supported by": "support_contact",
}

FINAL_SCOPE_FAMILIES = {
    "relative_vertical",
    "size_relative",
    "relative_horizontal",
    "proximity",
    "support_contact",
}

SUCCESS_FAMILIES = {"relative_vertical", "size_relative"}
CAVEATED_FAMILIES = {"relative_horizontal"}
CONTROL_FAMILIES = {"proximity"}
DIAGNOSTIC_FAMILIES = {"support_contact"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--h2-materialization-dir", type=Path, default=DEFAULT_H2_OFFICIAL_MATERIALIZATION_DIR)
    parser.add_argument("--h2-eval-dir", type=Path, default=DEFAULT_H2_OFFICIAL_EVAL_DIR)
    parser.add_argument("--validation-gt", type=Path, default=DEFAULT_VALIDATION_GT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def edge_key(row: dict[str, Any]) -> tuple[str, int | str, int | str, str]:
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    return (
        str(row.get("scan_id")),
        edge.get("subject_id"),
        edge.get("object_id"),
        str(predicate.get("predicate_label")),
    )


def family_for_predicate(predicate: str) -> str:
    return PREDICATE_TO_FAMILY.get(predicate, "out_of_scope")


def load_gt(path: Path) -> tuple[set[tuple[str, int, int, str]], Counter[str]]:
    gt_keys: set[tuple[str, int, int, str]] = set()
    gt_family_counts: Counter[str] = Counter()
    data = read_json(path)
    scans = data.get("scans", data if isinstance(data, list) else [])
    for scan in scans:
        scan_id = str(scan.get("scan"))
        for rel in scan.get("relationships", []):
            if not isinstance(rel, list) or len(rel) < 4:
                continue
            subject_id, object_id, _, predicate = rel[:4]
            predicate = str(predicate)
            family = family_for_predicate(predicate)
            if family not in FINAL_SCOPE_FAMILIES:
                continue
            gt_keys.add((scan_id, subject_id, object_id, predicate))
            gt_family_counts[family] += 1
    return gt_keys, gt_family_counts


def load_h2_official_keys(materialization_dir: Path, eval_dir: Path) -> tuple[set[tuple[str, Any, Any, str]], set[tuple[str, Any, Any, str]], Counter[str]]:
    candidate_to_key: dict[str, tuple[str, Any, Any, str]] = {}
    key_families: dict[tuple[str, Any, Any, str], str] = {}
    model_safe = materialization_dir / "model_safe_view.jsonl"
    if model_safe.exists():
        for row in iter_jsonl(model_safe):
            key = (str(row.get("scan_id")), row.get("subject_id"), row.get("object_id"), str(row.get("predicate_label")))
            candidate_to_key[str(row.get("candidate_id"))] = key
            key_families[key] = str(row.get("route_family"))

    ce_keys: set[tuple[str, Any, Any, str]] = set()
    scores_path = eval_dir / "prediction_scores.jsonl"
    if scores_path.exists():
        for row in iter_jsonl(scores_path):
            scores = row.get("scores", {})
            if "M4_TxG_compatibility" not in scores:
                continue
            key = candidate_to_key.get(str(row.get("candidate_id")))
            if key is not None:
                ce_keys.add(key)

    family_counter: Counter[str] = Counter()
    for family in key_families.values():
        family_counter[family] += 1
    return set(candidate_to_key.values()), ce_keys, family_counter


def source_paths(source_manifest_rows: list[dict[str, str]]) -> dict[str, dict[str, Path]]:
    paths: dict[str, dict[str, Path]] = {}
    for row in source_manifest_rows:
        source_id = row.get("source_id", "")
        paths[source_id] = {
            "adapter_predictions": REPO_ROOT / row.get("adapter_predictions", ""),
            "geometry_verification": REPO_ROOT / row.get("geometry_verification", ""),
        }
    return paths


def init_counter() -> Counter[str]:
    return Counter(
        {
            "source_prediction_rows": 0,
            "join_key_complete_rows": 0,
            "ranking_score_available": 0,
            "semantic_rank_available": 0,
            "predicate_rank_available": 0,
            "gt_positive_candidate_rows": 0,
            "h2_materialized_key_hits": 0,
            "h2_ce_score_hits": 0,
            "geometry_rows": 0,
            "geometry_available": 0,
            "geometry_checkable": 0,
            "p_geom_valid_available": 0,
            "consistency_score_available": 0,
            "status_satisfied": 0,
            "status_violated": 0,
            "status_uncertain": 0,
            "status_unsupported": 0,
            "strict_violation_label_rows": 0,
        }
    )


def inventory_sources(
    paths: dict[str, dict[str, Path]],
    gt_keys: set[tuple[str, int, int, str]],
    h2_keys: set[tuple[str, Any, Any, str]],
    h2_ce_keys: set[tuple[str, Any, Any, str]],
) -> tuple[dict[tuple[str, str], Counter[str]], dict[tuple[str, str], Counter[str]], dict[tuple[str, str], set[tuple[str, Any, Any, str]]], dict[str, Counter[str]]]:
    family_counts: dict[tuple[str, str], Counter[str]] = defaultdict(init_counter)
    predicate_counts: dict[tuple[str, str], Counter[str]] = defaultdict(init_counter)
    unique_keys: dict[tuple[str, str], set[tuple[str, Any, Any, str]]] = defaultdict(set)
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for source_id, source_path in paths.items():
        pred_path = source_path["adapter_predictions"]
        for row in iter_jsonl(pred_path):
            predicate = str(row.get("predicate", {}).get("predicate_label"))
            family = family_for_predicate(predicate)
            if family not in FINAL_SCOPE_FAMILIES:
                continue
            key = edge_key(row)
            family_key = (source_id, family)
            predicate_key = (source_id, f"{family}|{predicate}")
            for counter_key in [family_key, predicate_key]:
                counter = family_counts[counter_key] if counter_key == family_key else predicate_counts[counter_key]
                counter["source_prediction_rows"] += 1
                edge = row.get("edge", {})
                if row.get("scan_id") is not None and edge.get("subject_id") is not None and edge.get("object_id") is not None and predicate:
                    counter["join_key_complete_rows"] += 1
                scores = row.get("scores", {})
                ranks = row.get("ranks", {})
                if safe_float(scores.get("ranking_score")) is not None:
                    counter["ranking_score_available"] += 1
                if ranks.get("semantic_rank_in_subgraph") is not None:
                    counter["semantic_rank_available"] += 1
                if ranks.get("predicate_rank_for_pair") is not None:
                    counter["predicate_rank_available"] += 1
                if key in gt_keys:
                    counter["gt_positive_candidate_rows"] += 1
                if key in h2_keys:
                    counter["h2_materialized_key_hits"] += 1
                if key in h2_ce_keys:
                    counter["h2_ce_score_hits"] += 1
            unique_keys[family_key].add(key)
            source_counts[source_id]["source_prediction_rows_in_scope"] += 1

        geom_path = source_path["geometry_verification"]
        for row in iter_jsonl(geom_path):
            predicate = str(row.get("predicate", {}).get("predicate_label"))
            family = family_for_predicate(predicate)
            if family not in FINAL_SCOPE_FAMILIES:
                continue
            for counter_key in [(source_id, family), (source_id, f"{family}|{predicate}")]:
                counter = family_counts[counter_key] if "|" not in counter_key[1] else predicate_counts[counter_key]
                counter["geometry_rows"] += 1
                geometry = row.get("geometry", {})
                verification = row.get("verification", {})
                quality = row.get("quality", {})
                calibration = row.get("calibration", {})
                if geometry.get("geometry_available") is True or quality.get("geometry_available") is True:
                    counter["geometry_available"] += 1
                if verification.get("is_geometry_checkable") is True or quality.get("geometry_checkable") is True:
                    counter["geometry_checkable"] += 1
                if safe_float(calibration.get("p_geom_valid")) is not None:
                    counter["p_geom_valid_available"] += 1
                if safe_float(verification.get("consistency_score")) is not None or safe_float(row.get("consistency_score")) is not None:
                    counter["consistency_score_available"] += 1
                status = str(verification.get("verification_status") or row.get("verification_status") or "unknown")
                if status in {"satisfied", "violated", "uncertain", "unsupported"}:
                    counter[f"status_{status}"] += 1
                if status in {"satisfied", "violated"}:
                    counter["strict_violation_label_rows"] += 1
    return family_counts, predicate_counts, unique_keys, source_counts


def ratio(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return float(numerator) / float(denominator)


def route_policy(family: str) -> tuple[str, str]:
    if family in SUCCESS_FAMILIES:
        return "primary_bridge_candidate", "include_after_source_wide_Ce_materialization"
    if family in CAVEATED_FAMILIES:
        return "caveated_bridge_candidate", "include_as_separate_or_caveated_after_source_wide_Ce_materialization"
    if family in CONTROL_FAMILIES:
        return "geometry_only_control", "needs_source_inventory_or_source_candidates"
    if family in DIAGNOSTIC_FAMILIES:
        return "diagnostic_only", "exclude_from_success_aggregation"
    return "future", "deferred"


def family_rows(
    family_counts: dict[tuple[str, str], Counter[str]],
    unique_keys: dict[tuple[str, str], set[tuple[str, Any, Any, str]]],
    gt_family_counts: Counter[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, family in sorted(family_counts):
        if "|" in family:
            continue
        counts = family_counts[(source_id, family)]
        total = counts["source_prediction_rows"]
        role, inclusion = route_policy(family)
        recall_ready = total > 0 and counts["ranking_score_available"] == total and counts["gt_positive_candidate_rows"] > 0
        h001_violation_ready = counts["p_geom_valid_available"] > 0 or counts["strict_violation_label_rows"] > 0
        h2_ce_direct_ready = counts["h2_ce_score_hits"] == total and total > 0
        if family == "support_contact":
            final_status = "diagnostic_only_no_success_metric"
        elif not h2_ce_direct_ready:
            final_status = "needs_source_wide_Ce_materialization_before_reranking_metric"
        elif recall_ready:
            final_status = "ready_for_metric_freeze"
        else:
            final_status = "blocked_missing_recall_inputs"
        rows.append(
            {
                "source_id": source_id,
                "route_family": family,
                "route_policy": role,
                "inclusion": inclusion,
                "source_prediction_rows": total,
                "unique_join_keys": len(unique_keys[(source_id, family)]),
                "duplicate_join_key_rows": max(0, total - len(unique_keys[(source_id, family)])),
                "join_key_complete_rate": f"{ratio(counts['join_key_complete_rows'], total):.6f}",
                "ranking_score_available_rate": f"{ratio(counts['ranking_score_available'], total):.6f}",
                "semantic_rank_available_rate": f"{ratio(counts['semantic_rank_available'], total):.6f}",
                "gt_positive_candidate_rows": counts["gt_positive_candidate_rows"],
                "gt_family_total": gt_family_counts.get(family, 0),
                "recall_at_k_computable_now": str(recall_ready),
                "geometry_rows": counts["geometry_rows"],
                "geometry_checkable_rate": f"{ratio(counts['geometry_checkable'], counts['geometry_rows']):.6f}",
                "p_geom_valid_available_rate": f"{ratio(counts['p_geom_valid_available'], counts['geometry_rows']):.6f}",
                "strict_violation_label_rows": counts["strict_violation_label_rows"],
                "h001_violation_at_k_computable_now": str(h001_violation_ready),
                "h2_materialized_key_hits": counts["h2_materialized_key_hits"],
                "h2_ce_score_hits": counts["h2_ce_score_hits"],
                "h2_ce_direct_join_rate": f"{ratio(counts['h2_ce_score_hits'], total):.6f}",
                "source_wide_Ce_required": str(not h2_ce_direct_ready),
                "reranking_metric_status": final_status,
            }
        )
    return rows


def predicate_rows(predicate_counts: dict[tuple[str, str], Counter[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (source_id, family_predicate), counts in sorted(predicate_counts.items()):
        if "|" not in family_predicate:
            continue
        family, predicate = family_predicate.split("|", 1)
        total = counts["source_prediction_rows"]
        rows.append(
            {
                "source_id": source_id,
                "route_family": family,
                "predicate_label": predicate,
                "source_prediction_rows": total,
                "ranking_score_available_rate": f"{ratio(counts['ranking_score_available'], total):.6f}",
                "gt_positive_candidate_rows": counts["gt_positive_candidate_rows"],
                "geometry_checkable_rate": f"{ratio(counts['geometry_checkable'], counts['geometry_rows']):.6f}",
                "p_geom_valid_available_rate": f"{ratio(counts['p_geom_valid_available'], counts['geometry_rows']):.6f}",
                "status_satisfied": counts["status_satisfied"],
                "status_violated": counts["status_violated"],
                "status_uncertain": counts["status_uncertain"],
                "status_unsupported": counts["status_unsupported"],
                "h2_ce_score_hits": counts["h2_ce_score_hits"],
                "h2_ce_direct_join_rate": f"{ratio(counts['h2_ce_score_hits'], total):.6f}",
            }
        )
    return rows


def metric_readiness_rows(family_inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in family_inventory:
        family = row["route_family"]
        source_id = row["source_id"]
        support_diag = family == "support_contact"
        ce_ready = row["reranking_metric_status"] == "ready_for_metric_freeze"
        rows.append(
            {
                "source_id": source_id,
                "route_family": family,
                "Recall@K_S0_source_score": "ready" if row["recall_at_k_computable_now"] == "True" else "blocked",
                "Violation@K_S0_or_H001_geometry": "diagnostic_only" if support_diag and row["h001_violation_at_k_computable_now"] == "True" else ("ready" if row["h001_violation_at_k_computable_now"] == "True" else "blocked"),
                "Recall@K_S2_source_x_Ce": "ready" if ce_ready else "blocked_needs_source_wide_Ce_materialization",
                "Violation@K_S2_source_x_Ce": "diagnostic_only" if support_diag else ("ready" if ce_ready and row["h001_violation_at_k_computable_now"] == "True" else "blocked_needs_source_wide_Ce_or_violation_labels"),
                "success_aggregation": "excluded_diagnostic" if support_diag else ("candidate" if family in SUCCESS_FAMILIES else "caveated_or_control"),
                "next_requirement": "source-wide C_e materialization and metric freeze" if not ce_ready else "metric freeze",
            }
        )
    return rows


def join_key_audit_rows(paths: dict[str, dict[str, Path]], source_counts: dict[str, Counter[str]]) -> list[dict[str, Any]]:
    rows = []
    for source_id, source_path in sorted(paths.items()):
        rows.append(
            {
                "source_id": source_id,
                "adapter_predictions": rel_path(source_path["adapter_predictions"]),
                "geometry_verification": rel_path(source_path["geometry_verification"]),
                "adapter_predictions_exists": source_path["adapter_predictions"].exists(),
                "geometry_verification_exists": source_path["geometry_verification"].exists(),
                "source_prediction_rows_in_scope": source_counts[source_id]["source_prediction_rows_in_scope"],
                "read_policy": "read_only",
            }
        )
    return rows


def validate_inputs(protocol_summary: dict[str, Any], protocol_dir: Path, source_paths_map: dict[str, dict[str, Path]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if protocol_summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol_summary.get("next_todo")})
    if protocol_summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors", "actual": protocol_summary.get("validation_errors")})
    if line_count(protocol_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "protocol_validation_error_file_not_empty"})
    decision = protocol_summary.get("decision", {})
    for key, expected in {
        "metrics_run": False,
        "official_test_usage": False,
        "C_e_must_exclude_Z_e": True,
        "support_contact_success_included": False,
    }.items():
        if decision.get(key) is not expected:
            errors.append({"error_type": "unexpected_protocol_decision", "key": key, "actual": decision.get(key), "expected": expected})
    for source_id, paths in source_paths_map.items():
        for name, path in paths.items():
            if not path.exists():
                errors.append({"error_type": "missing_source_file", "source_id": source_id, "file": name, "path": rel_path(path)})
    return errors


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    protocol_summary = read_json(args.protocol_dir / "summary.json")
    source_manifest_rows = read_csv(args.source_inventory_dir / "source_manifest_inventory.csv")
    paths = source_paths(source_manifest_rows)
    errors = validate_inputs(protocol_summary, args.protocol_dir, paths)

    gt_keys, gt_family_counts = load_gt(args.validation_gt)
    h2_keys, h2_ce_keys, h2_family_counts = load_h2_official_keys(args.h2_materialization_dir, args.h2_eval_dir)
    family_counts, predicate_counts, unique_keys, source_counts = inventory_sources(paths, gt_keys, h2_keys, h2_ce_keys)

    family_inventory = family_rows(family_counts, unique_keys, gt_family_counts)
    predicate_inventory = predicate_rows(predicate_counts)
    metric_readiness = metric_readiness_rows(family_inventory)
    join_audit = join_key_audit_rows(paths, source_counts)

    direct_ready_rows = [
        row for row in family_inventory
        if row["reranking_metric_status"] == "ready_for_metric_freeze"
    ]
    blocked_needs_ce = [
        row for row in family_inventory
        if row["source_wide_Ce_required"] == "True" and row["route_family"] != "support_contact"
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_source_reranking_inventory_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_source_reranking_source_inventory_inputs",
        "input_artifacts": {
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
            "source_manifest_inventory": rel_path(args.source_inventory_dir / "source_manifest_inventory.csv"),
            "h2_official_materialization": rel_path(args.h2_materialization_dir),
            "h2_official_evaluation": rel_path(args.h2_eval_dir),
            "validation_gt": rel_path(args.validation_gt),
        },
        "inventory_summary": {
            "source_count": len(paths),
            "source_ids": sorted(paths),
            "gt_final_scope_rows": sum(gt_family_counts.values()),
            "h2_official_materialized_keys": len(h2_keys),
            "h2_official_ce_score_keys": len(h2_ce_keys),
            "h2_materialized_family_counts": dict(sorted(h2_family_counts.items())),
            "direct_source_reranking_metric_ready_family_source_rows": len(direct_ready_rows),
            "family_source_rows_needing_source_wide_Ce": len(blocked_needs_ce),
        },
        "decision": {
            "metrics_run": False,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "source_prediction_join_keys_available": not bool(errors),
            "source_score_and_rank_available": True,
            "recall_at_k_S0_source_score_computable": True,
            "S2_source_x_Ce_metric_ready_now": False,
            "reason_S2_not_ready": "Current H002 C_e scores cover official GT/counterfactual rows, not the full source prediction universe.",
            "next_stage": "source-wide candidate materialization protocol before reranking metric freeze",
        },
        "output_artifacts": {
            "summary": rel_path(out_dir / "summary.json"),
            "validation_errors": rel_path(out_dir / "validation_errors.jsonl"),
            "source_family_inventory": rel_path(out_dir / "source_family_inventory.csv"),
            "source_predicate_inventory": rel_path(out_dir / "source_predicate_inventory.csv"),
            "metric_readiness": rel_path(out_dir / "metric_readiness.csv"),
            "join_key_audit": rel_path(out_dir / "join_key_audit.csv"),
            "next_contract": rel_path(out_dir / "next_contract.json"),
            "report": rel_path(out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_materialization_protocol" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "next_task": "freeze source-wide C_e materialization protocol before running Recall@K or Violation@K",
        "must_include": [
            "source prediction universe keyed by scan_id/subject_id/object_id/predicate",
            "model-safe T_e and G_e blocks for source candidates",
            "hidden GT match and violation labels only for metric computation",
            "score contract S0/S1/S2/S3 and controls",
            "support_contact diagnostic exclusion from success aggregation",
        ],
        "must_not_do": [
            "run source reranking metrics from partial H2 GT/counterfactual C_e scores",
            "use official test",
            "put Z_e inside C_e",
            "promote support_contact as solved",
        ],
    }

    report_lines = [
        "# Source Reranking Source Inventory After Protocol Plan",
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
        "## Result",
        "",
        "Source prediction join keys, source scores, and ranks are available for VL-SAT and Open3DSG bridge sources.",
        "Recall@K for the source-score baseline is computable from source candidates and official validation GT.",
        "",
        "However, the planned S2_source_x_Ce bridge is not metric-ready yet because current H002 C_e scores cover",
        "official GT/counterfactual materialization rows, not the full source prediction universe.",
        "",
        "The next stage must define source-wide C_e materialization before any reranking metric run.",
    ]

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "source_family_inventory.csv", family_inventory)
    write_csv(out_dir / "source_predicate_inventory.csv", predicate_inventory)
    write_csv(out_dir / "metric_readiness.csv", metric_readiness)
    write_csv(out_dir / "join_key_audit.csv", join_audit)
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
