#!/usr/bin/env python3
"""Build train-set H002 RGA rows for the Open3DSG pilot scope."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterable


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
PILOT_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot"
DEFAULT_PREDICTIONS = PILOT_ROOT / "adapter/predictions.jsonl"
DEFAULT_GEOMETRY = PILOT_ROOT / "geometry/verification.jsonl"
DEFAULT_SUBSET = PILOT_ROOT / "source_contract/relationships_train_pilot.json"
DEFAULT_SOURCE_CONTRACT = PILOT_ROOT / "source_contract/source_contract.json"
DEFAULT_OUTPUT_DIR = PILOT_ROOT / "rga"

CHECKABLE_STATUSES = {"satisfied", "unsatisfied", "uncertain"}
TOP_KS = (50, 100)

SUPPORT_CONTACT = {"standing on", "lying on", "supported by"}
PROXIMITY = {"close by"}
RELATIVE_VERTICAL = {"higher than", "lower than"}
RELATIVE_HORIZONTAL = {"left", "right", "front", "behind"}
ATTACHMENT_DEFERRED = {"attached to", "hanging on", "connected to"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions-jsonl", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--geometry-jsonl", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--subset-json", type=Path, default=DEFAULT_SUBSET)
    parser.add_argument("--source-contract", type=Path, default=DEFAULT_SOURCE_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-id", default="open3dsg_train_pilot")
    parser.add_argument("--scope-id", default="open3dsg_train_pilot_100_subgraphs")
    parser.add_argument(
        "--queue-limit",
        type=int,
        default=0,
        help="Maximum rows per HL/LH queue. Use 0 to keep all queue rows.",
    )
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def nested_get(row: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    value: Any = row
    for part in path:
        if not isinstance(value, dict):
            return default
        value = value.get(part)
        if value is None:
            return default
    return value


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def predicate_family(label: str) -> str:
    if label in SUPPORT_CONTACT:
        return "support_contact"
    if label in PROXIMITY:
        return "proximity"
    if label in RELATIVE_VERTICAL:
        return "relative_vertical"
    if label in RELATIVE_HORIZONTAL:
        return "relative_horizontal"
    if label in ATTACHMENT_DEFERRED:
        return "attachment_deferred"
    return "unsupported_first_pass"


def h002_geometry_status(h001_status: str | None) -> str:
    if h001_status == "violated":
        return "unsatisfied"
    if h001_status in {"satisfied", "uncertain", "unsupported"}:
        return h001_status
    return "missing"


def geometry_axis(status: str) -> str:
    return {
        "satisfied": "H",
        "unsatisfied": "L",
        "uncertain": "U",
        "unsupported": "M",
        "missing": "M",
    }.get(status, "M")


def coverage_state(status: str) -> str:
    return {
        "satisfied": "covered_checkable",
        "unsatisfied": "covered_checkable",
        "uncertain": "covered_checkable_uncertain",
        "unsupported": "unsupported_family",
        "missing": "missing_geometry",
    }.get(status, "missing_geometry")


def rank_band(rank: int | None) -> str:
    if rank is None:
        return "rank_missing"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100_only"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def safe_mean(total: float, count: int) -> float | None:
    return total / count if count else None


def semantic_rank(row: dict[str, Any]) -> int | None:
    value = nested_get(row, ("ranks", "semantic_rank_in_subgraph"))
    if value is None:
        value = nested_get(row, ("semantic", "ranks", "semantic_rank_in_subgraph"))
    return to_int(value)


def prediction_id(row: dict[str, Any]) -> str:
    return str(row.get("prediction_id"))


def subgraph_id(row: dict[str, Any]) -> str:
    return str(row.get("subgraph_id"))


def subset_split_id(row: dict[str, Any]) -> int | None:
    value = row.get("subset_split_id")
    return to_int(value)


def edge_subject_id(row: dict[str, Any]) -> int | None:
    return to_int(nested_get(row, ("edge", "subject_id")))


def edge_object_id(row: dict[str, Any]) -> int | None:
    return to_int(nested_get(row, ("edge", "object_id")))


def prediction_label(row: dict[str, Any]) -> str:
    return str(nested_get(row, ("predicate", "predicate_label")))


def prediction_family(row: dict[str, Any]) -> str:
    family = nested_get(row, ("predicate", "predicate_family"))
    if family is not None:
        return str(family)
    return predicate_family(prediction_label(row))


def prediction_key(row: dict[str, Any]) -> tuple[str, int | None, int | None, int | None, str]:
    return (
        str(row.get("scan_id")),
        subset_split_id(row),
        edge_subject_id(row),
        edge_object_id(row),
        prediction_label(row),
    )


def prediction_pair_key(row: dict[str, Any]) -> tuple[str, int | None, int | None, int | None]:
    return prediction_key(row)[:4]


def load_context_counts(path: Path) -> tuple[Counter[str], int]:
    counts: Counter[str] = Counter()
    rows = 0
    for _, row in read_jsonl(path):
        rows += 1
        counts[subgraph_id(row)] += 1
    return counts, rows


def load_source_contract(path: Path) -> dict[str, Any]:
    path = as_abs(path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_ground_truth(path: Path) -> dict[str, Any]:
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    exact: dict[tuple[str, int, int, int, str], list[dict[str, Any]]] = defaultdict(list)
    by_pair: dict[tuple[str, int, int, int], list[dict[str, Any]]] = defaultdict(list)
    family_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    context_counts: Counter[str] = Counter()
    rows = 0

    for scan_entry in data.get("scans", []):
        scan_id = str(scan_entry["scan"])
        split_id = int(scan_entry["split"])
        current_subgraph_id = f"{scan_id}_{split_id}"
        for local_idx, rel in enumerate(scan_entry.get("relationships", [])):
            subject_id, object_id, predicate_id, label = rel[:4]
            family = predicate_family(str(label))
            gt_id = (
                f"{current_subgraph_id}:{local_idx}:"
                f"{int(subject_id)}:{int(object_id)}:{int(predicate_id)}"
            )
            gt_row = {
                "gt_id": gt_id,
                "scan_id": scan_id,
                "subset_split_id": split_id,
                "subgraph_id": current_subgraph_id,
                "subject_id": int(subject_id),
                "object_id": int(object_id),
                "raw_3dssg_predicate_id": int(predicate_id),
                "predicate_label": str(label),
                "predicate_family": family,
            }
            key = (
                scan_id,
                split_id,
                int(subject_id),
                int(object_id),
                str(label),
            )
            pair_key = key[:4]
            exact[key].append(gt_row)
            by_pair[pair_key].append(gt_row)
            family_counts[family] += 1
            label_counts[str(label)] += 1
            context_counts[current_subgraph_id] += 1
            rows += 1

    return {
        "exact": dict(exact),
        "by_pair": dict(by_pair),
        "family_counts": family_counts,
        "label_counts": label_counts,
        "context_counts": context_counts,
        "rows": rows,
        "contexts": len(context_counts),
    }


def match_ground_truth(prediction: dict[str, Any], gt: dict[str, Any]) -> dict[str, Any]:
    key = prediction_key(prediction)
    if None in key[:4]:
        return {
            "label_match": None,
            "label_match_status": "prediction_identity_missing",
            "family_match": None,
            "matched_gt_ids": [],
            "matched_predicates": [],
            "matched_families": [],
            "in_h001_denominator": None,
            "label_source": "direct_join_relationships_train_pilot",
        }

    exact_rows = gt["exact"].get(key, [])
    if exact_rows:
        return {
            "label_match": 1,
            "label_match_status": "exact_match",
            "family_match": 1,
            "matched_gt_ids": [row["gt_id"] for row in exact_rows],
            "matched_predicates": [row["predicate_label"] for row in exact_rows],
            "matched_families": [row["predicate_family"] for row in exact_rows],
            "in_h001_denominator": True,
            "label_source": "direct_join_relationships_train_pilot",
        }

    pair_rows = gt["by_pair"].get(prediction_pair_key(prediction), [])
    if not pair_rows:
        return {
            "label_match": 0,
            "label_match_status": "no_gt_for_pair",
            "family_match": 0,
            "matched_gt_ids": [],
            "matched_predicates": [],
            "matched_families": [],
            "in_h001_denominator": False,
            "label_source": "direct_join_relationships_train_pilot",
        }

    family = prediction_family(prediction)
    family_rows = [row for row in pair_rows if row["predicate_family"] == family]
    if family_rows:
        return {
            "label_match": 0,
            "label_match_status": "family_match",
            "family_match": 1,
            "matched_gt_ids": [row["gt_id"] for row in family_rows],
            "matched_predicates": [row["predicate_label"] for row in family_rows],
            "matched_families": [row["predicate_family"] for row in family_rows],
            "in_h001_denominator": False,
            "label_source": "direct_join_relationships_train_pilot",
        }

    return {
        "label_match": 0,
        "label_match_status": "pair_has_other_predicate",
        "family_match": 0,
        "matched_gt_ids": [row["gt_id"] for row in pair_rows],
        "matched_predicates": [row["predicate_label"] for row in pair_rows],
        "matched_families": [row["predicate_family"] for row in pair_rows],
        "in_h001_denominator": False,
        "label_source": "direct_join_relationships_train_pilot",
    }


def semantic_score_norm(rank: int | None, context_count: int | None) -> float | None:
    if rank is None or context_count is None or context_count <= 0:
        return None
    if context_count == 1:
        return 1.0 if rank == 1 else None
    value = 1.0 - ((rank - 1) / (context_count - 1))
    return max(0.0, min(1.0, value))


def make_semantic_block(prediction: dict[str, Any], context_count: int | None) -> dict[str, Any]:
    rank = semantic_rank(prediction)
    norm = semantic_score_norm(rank, context_count)
    return {
        "semantic_score_raw": to_float(nested_get(prediction, ("scores", "ranking_score"))),
        "semantic_score_type": nested_get(prediction, ("scores", "ranking_score_type")),
        "semantic_score_norm": norm,
        "rank_in_context": rank,
        "predicate_rank_for_pair": to_int(nested_get(prediction, ("ranks", "predicate_rank_for_pair"))),
        "top50_semantic": rank is not None and rank <= 50,
        "top100_semantic": rank is not None and rank <= 100,
        "context_prediction_count": context_count,
        "normalization_rule": "rank_in_context_linear_v0",
    }


def make_geometry_block(geometry: dict[str, Any] | None) -> dict[str, Any]:
    if geometry is None:
        status = "missing"
        h001_status = None
        verification = {}
        geometry_block = {}
        calibration = {}
    else:
        h001_status = str(geometry.get("verification_status") or "missing")
        status = h002_geometry_status(h001_status)
        verification = geometry.get("verification") or {}
        geometry_block = geometry.get("geometry") or {}
        calibration = geometry.get("calibration") or {}

    consistency = to_float(
        (geometry or {}).get("consistency_score")
        if geometry is not None
        else None
    )
    p_geom_valid = to_float(calibration.get("p_geom_valid"))
    p_geom_invalid = to_float(calibration.get("p_geom_invalid"))
    return {
        "geometry_status": status,
        "h001_verification_status": h001_status,
        "geometry_available": bool(geometry_block.get("geometry_available", False)),
        "geometry_checkable": bool(verification.get("is_geometry_checkable", False)),
        "geometry_source": verification.get("geometry_source") or geometry_block.get("geometry_source"),
        "consistency_score": consistency,
        "geometry_residual_proxy": 1.0 - consistency if consistency is not None else None,
        "p_geom_valid": p_geom_valid,
        "p_geom_invalid": p_geom_invalid,
        "reason_codes": [str(item) for item in verification.get("reason_codes", [])],
        "raw_features": geometry_block.get("features"),
        "selected_policy": nested_get(geometry or {}, ("provenance", "selected_verification_policy")),
    }


def label_geometry_bucket(label: dict[str, Any], geometry_status: str) -> str:
    label_axis = "TP" if label.get("label_match") == 1 else "FP"
    if geometry_status == "satisfied":
        suffix = "GS"
    elif geometry_status == "unsatisfied":
        suffix = "GU"
    else:
        suffix = "GC"
    return f"RGA-{label_axis}-{suffix}"


def make_rga_block(semantic: dict[str, Any], geometry: dict[str, Any], label: dict[str, Any]) -> dict[str, Any]:
    status = str(geometry["geometry_status"])
    geom_axis = geometry_axis(status)
    top50_axis = "H" if semantic["top50_semantic"] else "L"
    top100_axis = "H" if semantic["top100_semantic"] else "L"
    semantic_norm = semantic.get("semantic_score_norm")
    p_geom_valid = geometry.get("p_geom_valid")
    disagreement = None
    underconfidence = None
    absolute_disagreement = None
    if semantic_norm is not None and p_geom_valid is not None:
        semantic_norm = float(semantic_norm)
        p_geom_valid = float(p_geom_valid)
        disagreement = max(0.0, semantic_norm - p_geom_valid)
        underconfidence = max(0.0, p_geom_valid - semantic_norm)
        absolute_disagreement = abs(semantic_norm - p_geom_valid)
    return {
        "bucket_top50": f"RGA-{top50_axis}{geom_axis}",
        "bucket_top100": f"RGA-{top100_axis}{geom_axis}",
        "geometry_axis": geom_axis,
        "semantic_axis_top50": top50_axis,
        "semantic_axis_top100": top100_axis,
        "label_geometry_bucket": label_geometry_bucket(label, status),
        "disagreement_score": disagreement,
        "underconfidence_score": underconfidence,
        "absolute_disagreement": absolute_disagreement,
        "coverage_state": coverage_state(status),
        "rank_band": rank_band(semantic.get("rank_in_context")),
    }


def make_h002_row(
    source_id: str,
    scope_id: str,
    prediction: dict[str, Any],
    geometry_row: dict[str, Any] | None,
    gt_match: dict[str, Any],
    context_count: int | None,
    input_paths: dict[str, str],
    created_at: str,
) -> dict[str, Any]:
    semantic = make_semantic_block(prediction, context_count)
    geometry = make_geometry_block(geometry_row)
    rga = make_rga_block(semantic, geometry, gt_match)
    scan_id = str(prediction.get("scan_id"))
    current_subgraph_id = subgraph_id(prediction)
    subject_id = edge_subject_id(prediction)
    object_id = edge_object_id(prediction)
    directed_pair_id = f"{scan_id}:{current_subgraph_id}:{subject_id}:{object_id}"

    return {
        "schema_version": "h002_rga_edge_v0",
        "record_type": "h002_rga_edge",
        "source": {
            "source_id": source_id,
            "baseline_name": prediction.get("baseline_name"),
            "baseline_run_id": prediction.get("baseline_run_id"),
            "split_name": prediction.get("split_name"),
            "scope_id": scope_id,
            "source_schema_version": prediction.get("schema_version"),
        },
        "identity": {
            "prediction_id": prediction_id(prediction),
            "scan_id": scan_id,
            "subgraph_id": current_subgraph_id,
            "subset_split_id": subset_split_id(prediction),
            "subject_id": subject_id,
            "object_id": object_id,
            "directed_pair_id": directed_pair_id,
            "row_key": prediction_id(prediction),
        },
        "edge": {
            "subject_label": nested_get(prediction, ("edge", "subject_label")),
            "object_label": nested_get(prediction, ("edge", "object_label")),
            "subject_node_index": to_int(nested_get(prediction, ("edge", "subject_node_index"))),
            "object_node_index": to_int(nested_get(prediction, ("edge", "object_node_index"))),
            "edge_index": to_int(nested_get(prediction, ("edge", "edge_index"))),
            "edge_source": nested_get(prediction, ("edge", "edge_source")),
        },
        "predicate": {
            "predicate_label": prediction_label(prediction),
            "predicate_family": prediction_family(prediction),
            "predicate_vocab": nested_get(prediction, ("predicate", "predicate_vocab")),
            "raw_3dssg_predicate_id": to_int(nested_get(prediction, ("predicate", "raw_3dssg_predicate_id"))),
            "source_predicate_index": to_int(nested_get(prediction, ("predicate", "open3dsg_predicate_index"))),
        },
        "semantic": semantic,
        "geometry": geometry,
        "label": gt_match,
        "rga": rga,
        "posterior": {
            "posterior_edge_valid": None,
            "posterior_model_id": None,
            "factor_contribution": None,
            "abstain_or_promote": None,
        },
        "provenance": {
            "created_by": "tools/train_rga_rows.py",
            "created_at": created_at,
            "input_prediction_path": input_paths["predictions"],
            "input_geometry_path": input_paths["geometry"],
            "input_failure_rows_path": None,
            "input_gt_path": input_paths["ground_truth"],
            "h001_joiner": nested_get(geometry_row or {}, ("provenance", "joiner")),
            "selected_verification_policy": nested_get(
                geometry_row or {}, ("provenance", "selected_verification_policy")
            ),
            "source_caveat": "Open3DSG train pilot; hypothesis-stage train-set diagnostic, not held-out paper result.",
            "notes": [
                "violated is mapped to unsatisfied for H002 RGA buckets",
                "p_geom_valid is geometry-only continuous evidence, not posterior_edge_valid",
            ],
        },
    }


def queue_hint(row: dict[str, Any], kind: str) -> str:
    match_status = row["label"]["label_match_status"]
    family = row["predicate"]["predicate_family"]
    if kind == "HL":
        if match_status == "exact_match":
            return "exact_label_but_geometry_unsatisfied_review_geometry_or_annotation"
        if match_status == "family_match":
            return "semantic_overconfidence_family_granularity_review"
        if match_status == "pair_has_other_predicate":
            return "semantic_overconfidence_wrong_predicate_on_gt_pair"
        return "semantic_overconfidence_no_gt_pair_candidate"

    if match_status == "exact_match":
        return "semantic_underconfidence_exact_gt_geometry_supported"
    if match_status == "family_match":
        return "semantic_underconfidence_family_or_granularity_candidate"
    if match_status == "pair_has_other_predicate":
        return "geometry_supported_alternative_relation_on_gt_pair"
    if family == "proximity":
        return "dense_proximity_or_annotation_sparsity_candidate"
    if family == "relative_vertical":
        return "vertical_order_annotation_sparsity_candidate"
    if family == "support_contact":
        return "support_contact_missed_candidate_needs_endpoint_audit"
    return "needs_manual_audit"


def make_queue_row(row: dict[str, Any], kind: str) -> dict[str, Any]:
    return {
        "audit_status": "needs_train_rga_audit",
        "queue_kind": kind,
        "source_id": row["source"]["source_id"],
        "prediction_id": row["identity"]["prediction_id"],
        "scan_id": row["identity"]["scan_id"],
        "subgraph_id": row["identity"]["subgraph_id"],
        "subject_id": row["identity"]["subject_id"],
        "subject_label": row["edge"]["subject_label"],
        "object_id": row["identity"]["object_id"],
        "object_label": row["edge"]["object_label"],
        "predicate_label": row["predicate"]["predicate_label"],
        "predicate_family": row["predicate"]["predicate_family"],
        "semantic_rank": row["semantic"]["rank_in_context"],
        "semantic_score_raw": row["semantic"]["semantic_score_raw"],
        "semantic_score_norm": row["semantic"]["semantic_score_norm"],
        "rank_band": row["rga"]["rank_band"],
        "geometry_status": row["geometry"]["geometry_status"],
        "h001_verification_status": row["geometry"]["h001_verification_status"],
        "consistency_score": row["geometry"]["consistency_score"],
        "p_geom_valid": row["geometry"]["p_geom_valid"],
        "reason_codes": row["geometry"]["reason_codes"],
        "label_match_status": row["label"]["label_match_status"],
        "matched_gt_ids": row["label"]["matched_gt_ids"],
        "matched_predicates": row["label"]["matched_predicates"],
        "bucket_top50": row["rga"]["bucket_top50"],
        "bucket_top100": row["rga"]["bucket_top100"],
        "label_geometry_bucket": row["rga"]["label_geometry_bucket"],
        "disagreement_score": row["rga"]["disagreement_score"],
        "underconfidence_score": row["rga"]["underconfidence_score"],
        "machine_hint": queue_hint(row, kind),
    }


def queue_sort_key(row: dict[str, Any], kind: str) -> tuple[Any, ...]:
    rank = row.get("semantic_rank")
    rank_value = int(rank) if rank is not None else 10**9
    if kind == "HL":
        disagreement = row.get("disagreement_score")
        p_geom_valid = row.get("p_geom_valid")
        return (
            rank_value,
            -(float(disagreement) if disagreement is not None else -1.0),
            float(p_geom_valid) if p_geom_valid is not None else 2.0,
            str(row["prediction_id"]),
        )
    underconfidence = row.get("underconfidence_score")
    p_geom_valid = row.get("p_geom_valid")
    return (
        -(float(underconfidence) if underconfidence is not None else -1.0),
        -(float(p_geom_valid) if p_geom_valid is not None else -1.0),
        rank_value,
        str(row["prediction_id"]),
    )


def empty_metric_state() -> dict[str, Any]:
    return {
        "total": 0,
        "covered": 0,
        "satisfied": 0,
        "unsatisfied": 0,
        "uncertain": 0,
        "unsupported": 0,
        "missing": 0,
        "overconfidence_sum": 0.0,
        "overconfidence_count": 0,
        "underconfidence_sum": 0.0,
        "underconfidence_count": 0,
        "abs_disagreement_sum": 0.0,
        "abs_disagreement_count": 0,
    }


def update_metric_state(state: dict[str, Any], row: dict[str, Any]) -> None:
    status = row["geometry"]["geometry_status"]
    state["total"] += 1
    state[status] += 1
    if status in CHECKABLE_STATUSES:
        state["covered"] += 1
    rga = row["rga"]
    if rga["disagreement_score"] is not None:
        state["overconfidence_sum"] += float(rga["disagreement_score"])
        state["overconfidence_count"] += 1
    if rga["underconfidence_score"] is not None:
        state["underconfidence_sum"] += float(rga["underconfidence_score"])
        state["underconfidence_count"] += 1
    if rga["absolute_disagreement"] is not None:
        state["abs_disagreement_sum"] += float(rga["absolute_disagreement"])
        state["abs_disagreement_count"] += 1


def finalize_metric_state(state: dict[str, Any], prefix: str) -> dict[str, Any]:
    covered = state["covered"]
    total = state["total"]
    return {
        f"{prefix}_total": total,
        f"{prefix}_covered": covered,
        f"{prefix}_satisfied": state["satisfied"],
        f"{prefix}_unsatisfied": state["unsatisfied"],
        f"{prefix}_uncertain": state["uncertain"],
        f"{prefix}_unsupported": state["unsupported"],
        f"{prefix}_missing": state["missing"],
        f"{prefix}_coverage": safe_rate(covered, total),
        f"{prefix}_valid_rate": safe_rate(state["satisfied"], covered),
        f"{prefix}_hl_or_ll_rate": safe_rate(state["unsatisfied"], covered),
        f"{prefix}_uncertain_rate": safe_rate(state["uncertain"], covered),
        f"{prefix}_nonviolated_rate": safe_rate(state["satisfied"] + state["uncertain"], covered),
        f"{prefix}_unsupported_rate": safe_rate(state["unsupported"], total),
        f"{prefix}_missing_rate": safe_rate(state["missing"], total),
        f"{prefix}_overconfidence_mean": safe_mean(
            state["overconfidence_sum"], state["overconfidence_count"]
        ),
        f"{prefix}_underconfidence_mean": safe_mean(
            state["underconfidence_sum"], state["underconfidence_count"]
        ),
        f"{prefix}_abs_disagreement_mean": safe_mean(
            state["abs_disagreement_sum"], state["abs_disagreement_count"]
        ),
        f"{prefix}_continuous_count": state["abs_disagreement_count"],
    }


def serial_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def serial_nested_counter(mapping: dict[Any, Counter[Any]]) -> dict[str, dict[str, int]]:
    return {str(key): serial_counter(value) for key, value in sorted(mapping.items(), key=lambda item: str(item[0]))}


def build_rows(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    predictions_path = as_abs(args.predictions_jsonl)
    geometry_path = as_abs(args.geometry_jsonl)
    subset_path = as_abs(args.subset_json)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    context_counts, prediction_count_first_pass = load_context_counts(predictions_path)
    gt = load_ground_truth(subset_path)
    source_contract = load_source_contract(args.source_contract)
    created_at = datetime.now(timezone.utc).isoformat()
    input_paths = {
        "predictions": rel_path(predictions_path),
        "geometry": rel_path(geometry_path),
        "ground_truth": rel_path(subset_path),
        "source_contract": rel_path(args.source_contract),
    }

    match_rows_path = output_dir / "match_rows.jsonl"
    hl_queue: list[dict[str, Any]] = []
    lh_queue: list[dict[str, Any]] = []
    validation_errors: list[str] = []

    counts = Counter()
    by_family_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_family_bucket_top100: dict[str, Counter[str]] = defaultdict(Counter)
    by_family_label_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_label_geometry_bucket: Counter[str] = Counter()
    by_label_status: Counter[str] = Counter()
    by_rank_band: Counter[str] = Counter()
    by_rga_top50: Counter[str] = Counter()
    by_rga_top100: Counter[str] = Counter()
    label_geometry_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    lh_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    lh_by_rank_band: dict[str, Counter[str]] = defaultdict(Counter)
    lh_by_match_status: dict[str, Counter[str]] = defaultdict(Counter)
    hl_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    hl_by_match_status: dict[str, Counter[str]] = defaultdict(Counter)
    high_metrics = {k: empty_metric_state() for k in TOP_KS}
    tail_metrics = {k: empty_metric_state() for k in TOP_KS}
    row_count = 0
    geometry_count = 0
    prediction_geometry_mismatches = 0
    missing_identity = 0
    rank_gt_context = 0

    with match_rows_path.open("w", encoding="utf-8") as output:
        pred_iter = read_jsonl(predictions_path)
        geom_iter = read_jsonl(geometry_path)
        for pred_item, geom_item in zip_longest(pred_iter, geom_iter):
            if pred_item is None:
                geometry_count += 1
                validation_errors.append("extra_geometry_row")
                continue
            pred_line_no, prediction = pred_item
            geometry_row = None
            if geom_item is not None:
                _, geometry_row = geom_item
                geometry_count += 1

            pred_id = prediction_id(prediction)
            if geometry_row is not None and pred_id != prediction_id(geometry_row):
                prediction_geometry_mismatches += 1
                validation_errors.append(
                    f"prediction_geometry_id_mismatch:line={pred_line_no}:prediction_id={pred_id}:geometry_id={prediction_id(geometry_row)}"
                )
                geometry_row = None
            if None in prediction_key(prediction)[:4]:
                missing_identity += 1

            current_subgraph_id = subgraph_id(prediction)
            context_count = context_counts.get(current_subgraph_id)
            rank = semantic_rank(prediction)
            if rank is not None and context_count is not None and rank > context_count:
                rank_gt_context += 1

            gt_match = match_ground_truth(prediction, gt)
            row = make_h002_row(
                args.source_id,
                args.scope_id,
                prediction,
                geometry_row,
                gt_match,
                context_count,
                input_paths,
                created_at,
            )
            output.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
            row_count += 1

            family = row["predicate"]["predicate_family"]
            status = row["geometry"]["geometry_status"]
            bucket50 = row["rga"]["bucket_top50"]
            bucket100 = row["rga"]["bucket_top100"]
            label_status = row["label"]["label_match_status"]
            label_geom_bucket = row["rga"]["label_geometry_bucket"]
            band = row["rga"]["rank_band"]

            counts["rows"] += 1
            counts[f"geometry_status:{status}"] += 1
            counts[f"h001_status:{row['geometry']['h001_verification_status']}"] += 1
            counts[f"predicate_family:{family}"] += 1
            counts[f"label_status:{label_status}"] += 1
            counts[f"rga_top50:{bucket50}"] += 1
            counts[f"rga_top100:{bucket100}"] += 1
            counts[f"label_geometry:{label_geom_bucket}"] += 1
            counts[f"rank_band:{band}"] += 1
            if row["geometry"]["p_geom_valid"] is not None:
                counts["p_geom_valid_non_null"] += 1
            else:
                counts["p_geom_valid_null"] += 1
            by_family_status[family][status] += 1
            by_family_bucket_top100[family][bucket100] += 1
            by_family_label_status[family][label_status] += 1
            by_label_geometry_bucket[label_geom_bucket] += 1
            by_label_status[label_status] += 1
            by_rank_band[band] += 1
            by_rga_top50[bucket50] += 1
            by_rga_top100[bucket100] += 1
            label_geometry_by_family[family][label_geom_bucket] += 1

            for k in TOP_KS:
                if rank is not None and rank <= k:
                    update_metric_state(high_metrics[k], row)
                elif rank is not None and rank > k:
                    update_metric_state(tail_metrics[k], row)

            if rank is not None and rank <= 100 and status == "unsatisfied":
                queue_row = make_queue_row(row, "HL")
                hl_queue.append(queue_row)
                hl_by_family[family][label_status] += 1
                hl_by_match_status[label_status][family] += 1
            if rank is not None and rank > 100 and status == "satisfied":
                queue_row = make_queue_row(row, "LH")
                lh_queue.append(queue_row)
                lh_by_family[family][label_status] += 1
                lh_by_rank_band[band][label_status] += 1
                lh_by_match_status[label_status][family] += 1

    if prediction_count_first_pass != row_count:
        validation_errors.append(
            f"first_second_pass_prediction_count_mismatch:first={prediction_count_first_pass}:second={row_count}"
        )
    if row_count != geometry_count:
        validation_errors.append(f"prediction_geometry_count_mismatch:predictions={row_count}:geometry={geometry_count}")
    if prediction_geometry_mismatches:
        validation_errors.append(f"prediction_geometry_mismatches:{prediction_geometry_mismatches}")
    if missing_identity:
        validation_errors.append(f"missing_identity_rows:{missing_identity}")
    if rank_gt_context:
        validation_errors.append(f"rank_gt_context_count:{rank_gt_context}")

    hl_queue = sorted(hl_queue, key=lambda row: queue_sort_key(row, "HL"))
    lh_queue = sorted(lh_queue, key=lambda row: queue_sort_key(row, "LH"))
    if args.queue_limit > 0:
        hl_queue = hl_queue[: args.queue_limit]
        lh_queue = lh_queue[: args.queue_limit]

    metrics_by_k: dict[str, Any] = {}
    for k in TOP_KS:
        high = finalize_metric_state(high_metrics[k], f"top{k}")
        tail = finalize_metric_state(tail_metrics[k], f"tail_gt{k}")
        metrics_by_k[str(k)] = {
            "high_semantic": {
                **high,
                f"rga_hl_at_{k}": high[f"top{k}_hl_or_ll_rate"],
                f"rga_valid_at_{k}": high[f"top{k}_valid_rate"],
                f"rga_nonviolated_at_{k}": high[f"top{k}_nonviolated_rate"],
                f"rga_uncertain_at_{k}": high[f"top{k}_uncertain_rate"],
                f"rga_coverage_at_{k}": high[f"top{k}_coverage"],
            },
            "low_semantic_tail": {
                **tail,
                f"rga_lh_tail_at_{k}": tail[f"tail_gt{k}_valid_rate"],
                f"rga_ll_tail_at_{k}": tail[f"tail_gt{k}_hl_or_ll_rate"],
                f"rga_lu_tail_at_{k}": tail[f"tail_gt{k}_uncertain_rate"],
                f"rga_tail_coverage_at_{k}": tail[f"tail_gt{k}_coverage"],
            },
        }

    summary = {
        "schema_version": "h002_train_rga_rows_v0",
        "source_id": args.source_id,
        "scope_id": args.scope_id,
        "created_at": created_at,
        "status": "ready" if not validation_errors else "blocked",
        "input_paths": input_paths,
        "output_paths": {
            "match_rows": rel_path(match_rows_path),
            "train_hl_queue": rel_path(output_dir / "train_hl_queue.jsonl"),
            "train_lh_queue": rel_path(output_dir / "train_lh_queue.jsonl"),
            "report": rel_path(output_dir / "report.md"),
        },
        "input_counts": {
            "prediction_rows": row_count,
            "geometry_rows": geometry_count,
            "ground_truth_rows": gt["rows"],
            "ground_truth_contexts": gt["contexts"],
            "prediction_contexts": len(context_counts),
            "source_contract_selected_contexts": nested_get(source_contract, ("counts", "pilot_subset_contexts")),
        },
        "counts": {
            "geometry_status": {
                key.removeprefix("geometry_status:"): int(value)
                for key, value in sorted(counts.items())
                if key.startswith("geometry_status:")
            },
            "h001_status": {
                key.removeprefix("h001_status:"): int(value)
                for key, value in sorted(counts.items())
                if key.startswith("h001_status:")
            },
            "predicate_family": {
                key.removeprefix("predicate_family:"): int(value)
                for key, value in sorted(counts.items())
                if key.startswith("predicate_family:")
            },
            "label_status": serial_counter(by_label_status),
            "rga_top50": serial_counter(by_rga_top50),
            "rga_top100": serial_counter(by_rga_top100),
            "label_geometry_bucket": serial_counter(by_label_geometry_bucket),
            "rank_band": serial_counter(by_rank_band),
            "p_geom_valid_non_null": int(counts["p_geom_valid_non_null"]),
            "p_geom_valid_null": int(counts["p_geom_valid_null"]),
        },
        "ground_truth": {
            "predicate_family": serial_counter(gt["family_counts"]),
            "predicate_label": serial_counter(gt["label_counts"]),
        },
        "family_tables": {
            "geometry_status": serial_nested_counter(by_family_status),
            "rga_top100": serial_nested_counter(by_family_bucket_top100),
            "label_status": serial_nested_counter(by_family_label_status),
            "label_geometry_bucket": serial_nested_counter(label_geometry_by_family),
        },
        "metrics_by_k": metrics_by_k,
        "queues": {
            "hl_condition": "semantic_rank_in_subgraph <= 100 and geometry_status = unsatisfied",
            "lh_condition": "semantic_rank_in_subgraph > 100 and geometry_status = satisfied",
            "queue_limit": args.queue_limit,
            "hl_rows": len(hl_queue),
            "lh_rows": len(lh_queue),
            "hl_by_family": serial_nested_counter(hl_by_family),
            "hl_by_match_status": serial_nested_counter(hl_by_match_status),
            "lh_by_family": serial_nested_counter(lh_by_family),
            "lh_by_rank_band": serial_nested_counter(lh_by_rank_band),
            "lh_by_match_status": serial_nested_counter(lh_by_match_status),
        },
        "validation": {
            "prediction_count_first_pass": prediction_count_first_pass,
            "rows_written": row_count,
            "geometry_rows_seen": geometry_count,
            "prediction_geometry_mismatches": prediction_geometry_mismatches,
            "missing_identity_rows": missing_identity,
            "rank_gt_context_rows": rank_gt_context,
            "validation_errors": validation_errors[:100],
            "validation_error_count": len(validation_errors),
        },
        "boundary": {
            "split": "train pilot only",
            "not_paper_result": True,
            "geometry_bucket_rule": "deterministic H001 status, with violated mapped to H002 unsatisfied",
            "continuous_score_rule": "p_geom_valid is geometry-only evidence used for disagreement, not the H002 posterior",
        },
    }
    return summary, hl_queue, lh_queue


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def make_report(summary: dict[str, Any]) -> str:
    metrics50 = summary["metrics_by_k"]["50"]
    metrics100 = summary["metrics_by_k"]["100"]
    top100 = metrics100["high_semantic"]
    tail100 = metrics100["low_semantic_tail"]

    lines = [
        "# H002 Train RGA Rows Report",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Scope",
        "",
        "| Item | Value |",
        "| --- | ---: |",
        f"| prediction rows | {summary['input_counts']['prediction_rows']} |",
        f"| geometry rows | {summary['input_counts']['geometry_rows']} |",
        f"| GT relation rows | {summary['input_counts']['ground_truth_rows']} |",
        f"| prediction contexts | {summary['input_counts']['prediction_contexts']} |",
        f"| GT contexts | {summary['input_counts']['ground_truth_contexts']} |",
        "",
        "This is train-pilot hypothesis evidence only. It is not a held-out paper result.",
        "",
        "## RGA Metrics",
        "",
        "| Metric | K=50 | K=100 |",
        "| --- | ---: | ---: |",
        f"| RGA-HL@K | {pct(metrics50['high_semantic']['rga_hl_at_50'])} | {pct(top100['rga_hl_at_100'])} |",
        f"| RGA-valid@K | {pct(metrics50['high_semantic']['rga_valid_at_50'])} | {pct(top100['rga_valid_at_100'])} |",
        f"| RGA-nonviolated@K | {pct(metrics50['high_semantic']['rga_nonviolated_at_50'])} | {pct(top100['rga_nonviolated_at_100'])} |",
        f"| RGA-uncertain@K | {pct(metrics50['high_semantic']['rga_uncertain_at_50'])} | {pct(top100['rga_uncertain_at_100'])} |",
        f"| RGA-coverage@K | {pct(metrics50['high_semantic']['rga_coverage_at_50'])} | {pct(top100['rga_coverage_at_100'])} |",
        f"| RGA-LH-tail@K | {pct(metrics50['low_semantic_tail']['rga_lh_tail_at_50'])} | {pct(tail100['rga_lh_tail_at_100'])} |",
        f"| RGA-LL-tail@K | {pct(metrics50['low_semantic_tail']['rga_ll_tail_at_50'])} | {pct(tail100['rga_ll_tail_at_100'])} |",
        f"| RGA-LU-tail@K | {pct(metrics50['low_semantic_tail']['rga_lu_tail_at_50'])} | {pct(tail100['rga_lu_tail_at_100'])} |",
        "",
        "## Top-100 Denominators",
        "",
        "| Group | Total | Covered | Satisfied | Unsatisfied | Uncertain | Unsupported | Missing |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| top100 | {top100['top100_total']} | {top100['top100_covered']} | "
            f"{top100['top100_satisfied']} | {top100['top100_unsatisfied']} | "
            f"{top100['top100_uncertain']} | {top100['top100_unsupported']} | {top100['top100_missing']} |"
        ),
        (
            f"| tail>100 | {tail100['tail_gt100_total']} | {tail100['tail_gt100_covered']} | "
            f"{tail100['tail_gt100_satisfied']} | {tail100['tail_gt100_unsatisfied']} | "
            f"{tail100['tail_gt100_uncertain']} | {tail100['tail_gt100_unsupported']} | {tail100['tail_gt100_missing']} |"
        ),
        "",
        "## Geometry Status",
        "",
        "| Status | Rows |",
        "| --- | ---: |",
    ]
    for status, count in summary["counts"]["geometry_status"].items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(["", "## Label-Geometry Buckets", "", "| Bucket | Rows |", "| --- | ---: |"])
    for bucket, count in summary["counts"]["label_geometry_bucket"].items():
        lines.append(f"| `{bucket}` | {count} |")

    lines.extend(["", "## Queue Counts", "", "| Queue | Rows | Condition |", "| --- | ---: | --- |"])
    lines.append(
        f"| HL | {summary['queues']['hl_rows']} | `{summary['queues']['hl_condition']}` |"
    )
    lines.append(
        f"| LH | {summary['queues']['lh_rows']} | `{summary['queues']['lh_condition']}` |"
    )

    lines.extend(
        [
            "",
            "## Validation",
            "",
            "| Check | Value |",
            "| --- | ---: |",
            f"| rows written | {summary['validation']['rows_written']} |",
            f"| prediction-geometry mismatches | {summary['validation']['prediction_geometry_mismatches']} |",
            f"| missing identity rows | {summary['validation']['missing_identity_rows']} |",
            f"| validation error count | {summary['validation']['validation_error_count']} |",
            "",
            "## Boundary",
            "",
            "- `violated` is mapped to H002 `unsatisfied`.",
            "- `p_geom_valid` remains geometry-only continuous evidence.",
            "- `posterior_edge_valid` is intentionally null in `match_rows.jsonl`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary, hl_queue, lh_queue = build_rows(args)
    write_json(output_dir / "train_rga_summary.json", summary)
    write_jsonl(output_dir / "train_hl_queue.jsonl", hl_queue)
    write_jsonl(output_dir / "train_lh_queue.jsonl", lh_queue)
    (output_dir / "report.md").write_text(make_report(summary), encoding="utf-8")

    print(
        f"status={summary['status']} rows={summary['input_counts']['prediction_rows']} "
        f"hl={summary['queues']['hl_rows']} lh={summary['queues']['lh_rows']} "
        f"output={output_dir}"
    )
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
