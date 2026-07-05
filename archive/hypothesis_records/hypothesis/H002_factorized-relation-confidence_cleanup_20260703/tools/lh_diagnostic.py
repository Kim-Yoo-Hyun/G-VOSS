#!/usr/bin/env python3
"""Diagnose low-semantic/high-geometry (RGA-LH) candidates for H002."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
GT_PATH = (
    REPO_ROOT
    / "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl"
)

SOURCES = {
    "vlsat": {
        "source_id": "vlsat",
        "prediction_path": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl",
        "geometry_path": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl",
        "source_caveat": "controlled full-validation source",
    },
    "open3dsg_recovery_relaxed_views_min2": {
        "source_id": "open3dsg_recovery_relaxed_views_min2",
        "prediction_path": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl",
        "geometry_path": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl",
        "source_caveat": (
            "recovery-policy variant; not unmodified Open3DSG preprocessing"
        ),
    },
}

H001_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
CHECKABLE_STATUSES = {"satisfied", "violated", "uncertain"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(SOURCES))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-stratum", type=int, default=3)
    return parser.parse_args()


def read_jsonl(path: Path):
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


def subset_split_id(row: dict[str, Any]) -> int:
    return int(row["subset_split_id"])


def gt_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]),
        subset_split_id(row),
        int(row["subject_id"]),
        int(row["object_id"]),
        str(row["predicate_label"]),
    )


def gt_pair_key(row: dict[str, Any]) -> tuple[str, int, int, int]:
    return gt_key(row)[:4]


def prediction_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]),
        subset_split_id(row),
        int(nested_get(row, ("edge", "subject_id"))),
        int(nested_get(row, ("edge", "object_id"))),
        str(nested_get(row, ("predicate", "predicate_label"))),
    )


def prediction_pair_key(row: dict[str, Any]) -> tuple[str, int, int, int]:
    return prediction_key(row)[:4]


def prediction_family(row: dict[str, Any]) -> str:
    return str(nested_get(row, ("predicate", "predicate_family")))


def prediction_id(row: dict[str, Any]) -> str:
    return str(row["prediction_id"])


def semantic_rank(row: dict[str, Any]) -> int | None:
    value = nested_get(row, ("ranks", "semantic_rank_in_subgraph"))
    if value is None:
        value = nested_get(row, ("semantic", "ranks", "semantic_rank_in_subgraph"))
    return int(value) if value is not None else None


def ranking_score(row: dict[str, Any]) -> float | None:
    value = nested_get(row, ("scores", "ranking_score"))
    if value is None:
        value = nested_get(row, ("semantic", "ranking_score"))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_ground_truth(path: Path) -> dict[str, Any]:
    exact: dict[tuple[str, int, int, int, str], list[str]] = {}
    by_pair: dict[tuple[str, int, int, int], list[dict[str, Any]]] = {}
    for _, row in read_jsonl(path):
        key = gt_key(row)
        exact.setdefault(key, []).append(str(row.get("gt_id") or ""))
        by_pair.setdefault(gt_pair_key(row), []).append(row)
    return {"exact": exact, "by_pair": by_pair}


def load_geometry(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    duplicate_ids = 0
    for _, row in read_jsonl(path):
        pred_id = prediction_id(row)
        if pred_id in records:
            duplicate_ids += 1
        verification = row.get("verification") or {}
        records[pred_id] = {
            "verification_status": str(row.get("verification_status") or "missing"),
            "consistency_score": row.get("consistency_score"),
            "p_geom_valid": nested_get(row, ("calibration", "p_geom_valid")),
            "reason_codes": [str(item) for item in verification.get("reason_codes", [])],
            "geometry_available": bool(nested_get(row, ("geometry", "geometry_available"), False)),
            "geometry_checkable": bool(verification.get("is_geometry_checkable")),
        }
    return {"records": records, "duplicate_ids": duplicate_ids}


def match_ground_truth(prediction: dict[str, Any], gt: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    key = prediction_key(prediction)
    exact_ids = gt["exact"].get(key, [])
    if exact_ids:
        return "exact_match", exact_ids, [key[4]]

    pair_rows = gt["by_pair"].get(prediction_pair_key(prediction), [])
    if not pair_rows:
        return "no_gt_for_pair", [], []

    family = prediction_family(prediction)
    family_rows = [row for row in pair_rows if str(row.get("predicate_family")) == family]
    if family_rows:
        return (
            "family_match",
            [str(row.get("gt_id") or "") for row in family_rows],
            [str(row.get("predicate_label")) for row in family_rows],
        )
    return (
        "pair_has_other_predicate",
        [str(row.get("gt_id") or "") for row in pair_rows],
        [str(row.get("predicate_label")) for row in pair_rows],
    )


def semantic_scope(rank: int | None) -> str:
    if rank is None:
        return "rank_missing"
    if rank <= 100:
        return "high_top100"
    return "low_tail_gt100"


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


def sample_sort_key(row: dict[str, Any]) -> tuple[int, float, str]:
    rank = row.get("semantic_rank")
    score = row.get("semantic_score")
    return (
        int(rank) if rank is not None else 10**9,
        -(float(score) if score is not None else -1.0),
        str(row["prediction_id"]),
    )


def lh_machine_hint(
    match_status: str,
    family: str,
    predicate_label: str,
    matched_predicates: list[str],
    reason_codes: list[str],
) -> str:
    if match_status == "exact_match":
        return "semantic_underconfidence_exact_gt_geometry_supported"
    if match_status == "family_match":
        return "semantic_underconfidence_family_or_granularity_candidate"
    if match_status == "pair_has_other_predicate":
        if family == "support_contact" and any(
            pred in {"attached to", "hanging on"} for pred in matched_predicates
        ):
            return "ontology_boundary_attachment_vs_support"
        return "label_granularity_or_alternative_relation_on_same_pair"
    if family == "proximity":
        return "dense_geometry_trivial_or_annotation_sparsity_candidate"
    if family == "relative_vertical":
        return "vertical_order_annotation_sparsity_candidate"
    if family == "support_contact":
        if any("support" in code or "subtype" in code for code in reason_codes):
            return "support_contact_missed_candidate_needs_endpoint_audit"
        return "support_contact_needs_mesh_or_visual_audit"
    return "needs_manual_audit"


def make_queue_row(
    source_id: str,
    prediction: dict[str, Any],
    geometry: dict[str, Any],
    match_status: str,
    matched_gt_ids: list[str],
    matched_predicates: list[str],
) -> dict[str, Any]:
    rank = semantic_rank(prediction)
    family = prediction_family(prediction)
    predicate_label = str(nested_get(prediction, ("predicate", "predicate_label")))
    reason_codes = [str(item) for item in geometry.get("reason_codes") or []]
    return {
        "audit_status": "needs_lh_visual_or_mesh_review",
        "source_id": source_id,
        "prediction_id": prediction_id(prediction),
        "scan_id": prediction.get("scan_id"),
        "subgraph_id": prediction.get("subgraph_id"),
        "subject_id": nested_get(prediction, ("edge", "subject_id")),
        "subject_label": nested_get(prediction, ("edge", "subject_label")),
        "object_id": nested_get(prediction, ("edge", "object_id")),
        "object_label": nested_get(prediction, ("edge", "object_label")),
        "predicate_label": predicate_label,
        "predicate_family": family,
        "semantic_rank": rank,
        "semantic_score": ranking_score(prediction),
        "semantic_scope": semantic_scope(rank),
        "rank_band": rank_band(rank),
        "match_status": match_status,
        "matched_gt_ids": matched_gt_ids,
        "matched_predicates": matched_predicates,
        "verification_status": geometry["verification_status"],
        "consistency_score": geometry.get("consistency_score"),
        "p_geom_valid": geometry.get("p_geom_valid"),
        "reason_codes": reason_codes,
        "lh_machine_hint": lh_machine_hint(
            match_status, family, predicate_label, matched_predicates, reason_codes
        ),
    }


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def summarize(source: dict[str, Any], per_stratum: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gt = load_ground_truth(GT_PATH)
    geometry_payload = load_geometry(source["geometry_path"])
    geometry_by_id = geometry_payload["records"]

    counts = Counter()
    geometry_by_scope = defaultdict(Counter)
    lh_by_family = defaultdict(Counter)
    lh_by_rank_band = defaultdict(Counter)
    lh_by_match_status = defaultdict(Counter)
    lh_by_family_rank = defaultdict(Counter)
    lh_by_family_match = defaultdict(Counter)
    lh_hints = Counter()
    strata: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    validation_errors: list[str] = []
    total_predictions = 0
    missing_geometry = 0

    for line_no, prediction in read_jsonl(source["prediction_path"]):
        total_predictions += 1
        pred_id = prediction_id(prediction)
        geometry = geometry_by_id.get(pred_id)
        if geometry is None:
            missing_geometry += 1
            continue

        family = prediction_family(prediction)
        if family not in H001_FAMILIES:
            continue

        rank = semantic_rank(prediction)
        scope = semantic_scope(rank)
        band = rank_band(rank)
        geometry_status = str(geometry["verification_status"])
        geometry_by_scope[scope][geometry_status] += 1
        counts[f"{scope}+{geometry_status}"] += 1

        try:
            match_status, matched_gt_ids, matched_predicates = match_ground_truth(prediction, gt)
        except Exception as exc:
            validation_errors.append(f"match_error:line={line_no}:prediction_id={pred_id}:{exc}")
            continue

        if scope == "high_top100":
            if geometry_status in CHECKABLE_STATUSES:
                counts["high_top100_checkable"] += 1
            if geometry_status == "violated":
                counts["rga_hl_top100"] += 1
            if geometry_status == "satisfied":
                counts["rga_hh_top100"] += 1
            if geometry_status == "uncertain":
                counts["rga_hu_top100"] += 1

        if scope == "low_tail_gt100":
            if geometry_status in CHECKABLE_STATUSES:
                counts["low_tail_checkable"] += 1
            if geometry_status == "satisfied":
                counts["rga_lh_tail"] += 1
            elif geometry_status == "violated":
                counts["rga_ll_tail"] += 1
            elif geometry_status == "uncertain":
                counts["rga_lu_tail"] += 1

        if scope != "low_tail_gt100" or geometry_status != "satisfied":
            continue

        lh_by_family[family][match_status] += 1
        lh_by_rank_band[band][match_status] += 1
        lh_by_match_status[match_status][family] += 1
        lh_by_family_rank[family][band] += 1
        lh_by_family_match[family][match_status] += 1

        queue_row = make_queue_row(
            source["source_id"],
            prediction,
            geometry,
            match_status,
            matched_gt_ids,
            matched_predicates,
        )
        lh_hints[queue_row["lh_machine_hint"]] += 1
        strata[(family, match_status, band)].append(queue_row)

    queue: list[dict[str, Any]] = []
    for key in sorted(strata):
        rows = sorted(strata[key], key=sample_sort_key)
        for row in rows[:per_stratum]:
            row = dict(row)
            row["stratum"] = {
                "predicate_family": key[0],
                "match_status": key[1],
                "rank_band": key[2],
            }
            queue.append(row)

    if missing_geometry:
        validation_errors.append(f"missing_geometry_rows:{missing_geometry}")
    if total_predictions != len(geometry_by_id):
        validation_errors.append(
            f"prediction_geometry_count_mismatch:predictions={total_predictions}:geometry={len(geometry_by_id)}"
        )

    high_den = counts["high_top100_checkable"]
    low_den = counts["low_tail_checkable"]
    summary = {
        "schema_version": "h002_lh_diagnostic_v0",
        "source_id": source["source_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "predictions": str(source["prediction_path"].relative_to(REPO_ROOT)),
            "geometry": str(source["geometry_path"].relative_to(REPO_ROOT)),
            "ground_truth": str(GT_PATH.relative_to(REPO_ROOT)),
        },
        "low_semantic_definition": {
            "primary": "semantic_rank_in_subgraph > 100",
            "rank_bands": [
                "rank_101_200",
                "rank_201_500",
                "rank_501_1000",
                "rank_gt1000",
            ],
            "high_reference": "semantic_rank_in_subgraph <= 100",
        },
        "target": {
            "families": sorted(H001_FAMILIES),
            "lh_condition": "rank > 100 and verification_status = satisfied",
            "hl_reference_condition": "rank <= 100 and verification_status = violated",
        },
        "input_counts": {
            "prediction_rows": total_predictions,
            "geometry_rows": len(geometry_by_id),
            "geometry_duplicate_ids": geometry_payload["duplicate_ids"],
        },
        "rga_counts": dict(sorted(counts.items())),
        "rates": {
            "rga_hl_top100_rate": safe_rate(counts["rga_hl_top100"], high_den),
            "rga_lh_tail_rate": safe_rate(counts["rga_lh_tail"], low_den),
            "rga_hh_top100_rate": safe_rate(counts["rga_hh_top100"], high_den),
            "rga_ll_tail_rate": safe_rate(counts["rga_ll_tail"], low_den),
            "rga_lu_tail_rate": safe_rate(counts["rga_lu_tail"], low_den),
        },
        "geometry_by_scope": {
            scope: dict(sorted(counter.items()))
            for scope, counter in sorted(geometry_by_scope.items())
        },
        "lh_by_family": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(lh_by_family.items())
        },
        "lh_by_rank_band": {
            band: dict(sorted(counter.items()))
            for band, counter in sorted(lh_by_rank_band.items())
        },
        "lh_by_match_status": {
            status: dict(sorted(counter.items()))
            for status, counter in sorted(lh_by_match_status.items())
        },
        "lh_by_family_rank": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(lh_by_family_rank.items())
        },
        "lh_by_family_match": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(lh_by_family_match.items())
        },
        "lh_machine_hint_counts": dict(sorted(lh_hints.items())),
        "sample_policy": {
            "type": "top_low-tail_rank_per_family_match_status_rank_band",
            "per_stratum": per_stratum,
            "sample_rows": len(queue),
        },
        "source_caveat": source["source_caveat"],
        "validation_errors": validation_errors[:100],
        "validation_error_count": len(validation_errors),
        "status": "ready" if not validation_errors else "blocked",
        "boundary": (
            "RGA-LH is a candidate-discovery and audit signal, not automatic graph "
            "promotion. Dense or trivial geometry relations must be audited separately."
        ),
    }
    return summary, queue


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = H002_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source = SOURCES[args.source]
    summary, queue = summarize(source, args.per_stratum)
    summary_path = output_dir / f"{args.source}_summary.json"
    queue_path = output_dir / f"{args.source}_queue.jsonl"

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with queue_path.open("w", encoding="utf-8") as handle:
        for row in queue:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    print(
        f"{summary['source_id']} status={summary['status']} "
        f"lh={summary['rga_counts'].get('rga_lh_tail', 0)} "
        f"hl={summary['rga_counts'].get('rga_hl_top100', 0)} "
        f"queue={len(queue)} output={output_dir}"
    )
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
