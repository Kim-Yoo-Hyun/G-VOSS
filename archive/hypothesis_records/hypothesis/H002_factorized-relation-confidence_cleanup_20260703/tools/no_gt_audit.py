#!/usr/bin/env python3
"""Sample no-GT geometry-satisfied rows for H002 annotation audit."""

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

TARGET_MATCH_STATUS = {"no_gt_for_pair", "pair_has_other_predicate"}
TARGET_GEOMETRY_STATUS = "satisfied"
H001_FAMILIES = {"support_contact", "proximity", "relative_vertical"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(SOURCES))
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--per-stratum", type=int, default=8)
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
    for _, row in read_jsonl(path):
        verification = row.get("verification") or {}
        records[prediction_id(row)] = {
            "verification_status": str(row.get("verification_status") or "missing"),
            "consistency_score": row.get("consistency_score"),
            "p_geom_valid": nested_get(row, ("calibration", "p_geom_valid")),
            "reason_codes": [str(item) for item in verification.get("reason_codes", [])],
            "geometry_source": verification.get("geometry_source")
            or nested_get(row, ("geometry", "geometry_source")),
            "geometry_checkable": bool(verification.get("is_geometry_checkable")),
        }
    return records


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


def top_scope(rank: int | None) -> str:
    if rank is None:
        return "rank_missing"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100_only"
    return "outside_top100"


def machine_hint(
    match_status: str,
    family: str,
    predicate_label: str,
    matched_predicates: list[str],
    reason_codes: list[str],
) -> str:
    if match_status == "pair_has_other_predicate":
        if predicate_label in matched_predicates:
            return "unexpected_exact_label_mismatch_check_key"
        if family == "proximity":
            return "label_granularity_or_relation_set_mismatch"
        return "alternative_relation_on_same_pair"
    if family == "proximity":
        return "annotation_sparsity_or_dense_proximity_relation"
    if family == "relative_vertical":
        return "annotation_sparsity_or_spatial_relation_ambiguity"
    if family == "support_contact":
        if any("subtype" in code or "support" in code for code in reason_codes):
            return "plausible_unlabeled_support_candidate"
        return "support_contact_needs_visual_or_point_audit"
    return "needs_manual_audit"


def sample_sort_key(row: dict[str, Any]) -> tuple[int, float, str]:
    rank = row.get("semantic_rank")
    score = row.get("semantic_score")
    return (
        int(rank) if rank is not None else 10**9,
        -(float(score) if score is not None else -1.0),
        str(row["prediction_id"]),
    )


def summarize(source: dict[str, Any], per_stratum: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gt = load_ground_truth(GT_PATH)
    geometry_by_id = load_geometry(source["geometry_path"])
    counts = Counter()
    counts_by_family = defaultdict(Counter)
    counts_by_top_scope = defaultdict(Counter)
    machine_hints = Counter()
    strata: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    validation_errors: list[str] = []
    total_predictions = 0

    for line_no, prediction in read_jsonl(source["prediction_path"]):
        total_predictions += 1
        pred_id = prediction_id(prediction)
        geometry = geometry_by_id.get(pred_id)
        if geometry is None:
            validation_errors.append(f"missing_geometry:line={line_no}:prediction_id={pred_id}")
            continue
        if geometry["verification_status"] != TARGET_GEOMETRY_STATUS:
            continue
        match_status, matched_gt_ids, matched_predicates = match_ground_truth(prediction, gt)
        if match_status not in TARGET_MATCH_STATUS:
            continue

        family = prediction_family(prediction)
        if family not in H001_FAMILIES:
            continue

        rank = semantic_rank(prediction)
        scope = top_scope(rank)
        predicate_label = str(nested_get(prediction, ("predicate", "predicate_label")))
        reason_codes = [str(item) for item in geometry.get("reason_codes") or []]
        hint = machine_hint(match_status, family, predicate_label, matched_predicates, reason_codes)

        counts[match_status] += 1
        counts_by_family[family][match_status] += 1
        counts_by_top_scope[scope][match_status] += 1
        machine_hints[hint] += 1

        row = {
            "source_id": source["source_id"],
            "prediction_id": pred_id,
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
            "top_scope": scope,
            "match_status": match_status,
            "matched_gt_ids": matched_gt_ids,
            "matched_predicates": matched_predicates,
            "verification_status": geometry["verification_status"],
            "consistency_score": geometry.get("consistency_score"),
            "p_geom_valid": geometry.get("p_geom_valid"),
            "reason_codes": reason_codes,
            "machine_hint": hint,
            "audit_status": "needs_visual_or_annotation_review",
        }
        strata[(family, match_status, scope)].append(row)

    queue: list[dict[str, Any]] = []
    for key in sorted(strata):
        rows = sorted(strata[key], key=sample_sort_key)
        for row in rows[:per_stratum]:
            row = dict(row)
            row["stratum"] = {
                "predicate_family": key[0],
                "match_status": key[1],
                "top_scope": key[2],
            }
            queue.append(row)

    summary = {
        "schema_version": "h002_no_gt_audit_summary_v0",
        "source_id": source["source_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "predictions": str(source["prediction_path"].relative_to(REPO_ROOT)),
            "geometry": str(source["geometry_path"].relative_to(REPO_ROOT)),
            "ground_truth": str(GT_PATH.relative_to(REPO_ROOT)),
        },
        "target": {
            "match_status": sorted(TARGET_MATCH_STATUS),
            "geometry_status": TARGET_GEOMETRY_STATUS,
            "families": sorted(H001_FAMILIES),
        },
        "input_counts": {
            "prediction_rows": total_predictions,
            "geometry_rows": len(geometry_by_id),
        },
        "target_counts": dict(sorted(counts.items())),
        "target_total": sum(counts.values()),
        "target_by_family": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(counts_by_family.items())
        },
        "target_by_top_scope": {
            scope: dict(sorted(counter.items()))
            for scope, counter in sorted(counts_by_top_scope.items())
        },
        "machine_hint_counts": dict(sorted(machine_hints.items())),
        "sample_policy": {
            "type": "top_semantic_rank_per_family_match_status_top_scope",
            "per_stratum": per_stratum,
            "sample_rows": len(queue),
        },
        "source_caveat": source["source_caveat"],
        "validation_errors": validation_errors[:100],
        "validation_error_count": len(validation_errors),
        "status": "ready" if not validation_errors else "blocked",
        "boundary": (
            "Machine hints are triage labels, not final visual-audit labels. "
            "This artifact samples candidate no-GT geometry-satisfied rows only."
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
        f"targets={summary['target_total']} sample={len(queue)} "
        f"summary={summary_path} queue={queue_path}"
    )
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
