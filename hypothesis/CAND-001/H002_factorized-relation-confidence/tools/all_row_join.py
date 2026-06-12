#!/usr/bin/env python3
"""All-row GT label and geometry-status join for H002 diagnostics."""

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

SCOPES = ("all_rows", "top50", "top100", "h001_families_all", "h001_families_top50", "h001_families_top100")
H001_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
TARGET_KEYS = (
    ("exact_match", "violated"),
    ("exact_match", "uncertain"),
    ("family_match", "violated"),
    ("family_match", "uncertain"),
    ("no_gt_for_pair", "satisfied"),
    ("pair_has_other_predicate", "satisfied"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(SOURCES))
    parser.add_argument("--output", required=True, type=Path)
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
    key = gt_key(row)
    return key[:4]


def prediction_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]),
        subset_split_id(row),
        int(nested_get(row, ("edge", "subject_id"))),
        int(nested_get(row, ("edge", "object_id"))),
        str(nested_get(row, ("predicate", "predicate_label"))),
    )


def prediction_pair_key(row: dict[str, Any]) -> tuple[str, int, int, int]:
    key = prediction_key(row)
    return key[:4]


def prediction_family(row: dict[str, Any]) -> str:
    return str(nested_get(row, ("predicate", "predicate_family")))


def prediction_id(row: dict[str, Any]) -> str:
    return str(row["prediction_id"])


def semantic_rank(row: dict[str, Any]) -> int | None:
    value = nested_get(row, ("ranks", "semantic_rank_in_subgraph"))
    if value is None:
        value = nested_get(row, ("semantic", "ranks", "semantic_rank_in_subgraph"))
    return int(value) if value is not None else None


def load_ground_truth(path: Path) -> dict[str, Any]:
    exact: dict[tuple[str, int, int, int, str], list[str]] = {}
    by_pair: dict[tuple[str, int, int, int], list[dict[str, Any]]] = {}
    by_family = Counter()
    for _, row in read_jsonl(path):
        key = gt_key(row)
        exact.setdefault(key, []).append(str(row.get("gt_id") or ""))
        by_pair.setdefault(gt_pair_key(row), []).append(row)
        by_family[str(row.get("predicate_family"))] += 1
    return {"exact": exact, "by_pair": by_pair, "by_family": by_family}


def load_geometry(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    duplicate_ids = 0
    for _, row in read_jsonl(path):
        pred_id = prediction_id(row)
        if pred_id in records:
            duplicate_ids += 1
        records[pred_id] = {
            "verification_status": str(row.get("verification_status") or "missing"),
            "geometry_available": bool(nested_get(row, ("geometry", "geometry_available"), False)),
            "geometry_checkable": bool(nested_get(row, ("verification", "is_geometry_checkable"), False)),
            "p_geom_valid": nested_get(row, ("calibration", "p_geom_valid")),
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


def empty_scope() -> dict[str, Any]:
    return {
        "rows": 0,
        "cross_tab": defaultdict(Counter),
        "label_status_counts": Counter(),
        "geometry_status_counts": Counter(),
        "family_counts": Counter(),
        "target_counts": Counter(),
        "target_by_family": defaultdict(Counter),
        "exact_match_total": 0,
        "exact_match_bad_geometry": 0,
        "label_positive_total": 0,
        "label_positive_bad_geometry": 0,
        "gt_negative_total": 0,
        "gt_negative_geometry_satisfied": 0,
        "geometry_supported_rows": 0,
    }


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def finalize_scope(scope: dict[str, Any]) -> dict[str, Any]:
    return {
        "rows": scope["rows"],
        "cross_tab": {
            label: dict(sorted(statuses.items()))
            for label, statuses in sorted(scope["cross_tab"].items())
        },
        "label_status_counts": dict(sorted(scope["label_status_counts"].items())),
        "geometry_status_counts": dict(sorted(scope["geometry_status_counts"].items())),
        "family_counts": dict(sorted(scope["family_counts"].items())),
        "target_counts": dict(sorted(scope["target_counts"].items())),
        "target_by_family": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(scope["target_by_family"].items())
        },
        "denominators": {
            "exact_match_total": scope["exact_match_total"],
            "label_positive_total": scope["label_positive_total"],
            "gt_negative_total": scope["gt_negative_total"],
            "geometry_supported_rows": scope["geometry_supported_rows"],
        },
        "rates": {
            "exact_match_bad_geometry_rate": safe_rate(
                scope["exact_match_bad_geometry"], scope["exact_match_total"]
            ),
            "label_positive_bad_geometry_rate": safe_rate(
                scope["label_positive_bad_geometry"], scope["label_positive_total"]
            ),
            "gt_negative_geometry_satisfied_rate": safe_rate(
                scope["gt_negative_geometry_satisfied"], scope["gt_negative_total"]
            ),
            "geometry_supported_share": safe_rate(
                scope["geometry_supported_rows"], scope["rows"]
            ),
        },
    }


def row_scopes(prediction: dict[str, Any]) -> tuple[str, ...]:
    scopes = ["all_rows"]
    rank = semantic_rank(prediction)
    family = prediction_family(prediction)
    if rank is not None and rank <= 50:
        scopes.append("top50")
    if rank is not None and rank <= 100:
        scopes.append("top100")
    if family in H001_FAMILIES:
        scopes.append("h001_families_all")
        if rank is not None and rank <= 50:
            scopes.append("h001_families_top50")
        if rank is not None and rank <= 100:
            scopes.append("h001_families_top100")
    return tuple(scopes)


def update_scope(
    scope: dict[str, Any],
    label_status: str,
    geometry_status: str,
    family: str,
) -> None:
    scope["rows"] += 1
    scope["cross_tab"][label_status][geometry_status] += 1
    scope["label_status_counts"][label_status] += 1
    scope["geometry_status_counts"][geometry_status] += 1
    scope["family_counts"][family] += 1

    target_key = f"{label_status}+{geometry_status}"
    if (label_status, geometry_status) in TARGET_KEYS:
        scope["target_counts"][target_key] += 1
        scope["target_by_family"][family][target_key] += 1

    if label_status == "exact_match":
        scope["exact_match_total"] += 1
        if geometry_status in {"violated", "uncertain"}:
            scope["exact_match_bad_geometry"] += 1
    if label_status in {"exact_match", "family_match"}:
        scope["label_positive_total"] += 1
        if geometry_status in {"violated", "uncertain"}:
            scope["label_positive_bad_geometry"] += 1
    if label_status in {"no_gt_for_pair", "pair_has_other_predicate"}:
        scope["gt_negative_total"] += 1
        if geometry_status == "satisfied":
            scope["gt_negative_geometry_satisfied"] += 1
    if geometry_status in {"satisfied", "uncertain", "violated"}:
        scope["geometry_supported_rows"] += 1


def summarize(source: dict[str, Any]) -> dict[str, Any]:
    gt = load_ground_truth(GT_PATH)
    geometry_payload = load_geometry(source["geometry_path"])
    geometry_by_id = geometry_payload["records"]
    scopes = {name: empty_scope() for name in SCOPES}
    validation_errors: list[str] = []
    missing_geometry = 0
    prediction_rows = 0

    for line_no, prediction in read_jsonl(source["prediction_path"]):
        prediction_rows += 1
        pred_id = prediction_id(prediction)
        geometry = geometry_by_id.get(pred_id)
        if geometry is None:
            missing_geometry += 1
            geometry_status = "missing"
        else:
            geometry_status = str(geometry["verification_status"])
        try:
            label_status, _, _ = match_ground_truth(prediction, gt)
        except Exception as exc:  # keep row-level context in compact validation.
            validation_errors.append(f"match_error:line={line_no}:prediction_id={pred_id}:{exc}")
            label_status = "match_error"
        family = prediction_family(prediction)
        for scope_name in row_scopes(prediction):
            update_scope(scopes[scope_name], label_status, geometry_status, family)

    if missing_geometry:
        validation_errors.append(f"missing_geometry_rows:{missing_geometry}")
    if prediction_rows != len(geometry_by_id):
        validation_errors.append(
            f"prediction_geometry_count_mismatch:predictions={prediction_rows}:geometry={len(geometry_by_id)}"
        )

    return {
        "schema_version": "h002_all_row_label_geometry_v0",
        "source_id": source["source_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "predictions": str(source["prediction_path"].relative_to(REPO_ROOT)),
            "geometry": str(source["geometry_path"].relative_to(REPO_ROOT)),
            "ground_truth": str(GT_PATH.relative_to(REPO_ROOT)),
        },
        "input_counts": {
            "prediction_rows": prediction_rows,
            "geometry_rows": len(geometry_by_id),
            "ground_truth_rows": sum(gt["by_family"].values()),
            "geometry_duplicate_ids": geometry_payload["duplicate_ids"],
        },
        "ground_truth_by_family": dict(sorted(gt["by_family"].items())),
        "scopes": {name: finalize_scope(scope) for name, scope in scopes.items()},
        "source_caveat": source["source_caveat"],
        "validation_errors": validation_errors[:100],
        "validation_error_count": len(validation_errors),
        "status": "ready" if not validation_errors else "blocked",
        "boundary": (
            "All-row direct GT join over prediction rows and H001 geometry rows. "
            "This is still hypothesis-stage evidence, not a paper experiment result."
        ),
    }


def main() -> int:
    args = parse_args()
    summary = summarize(SOURCES[args.source])
    output = args.output
    if not output.is_absolute():
        output = H002_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        f"{summary['source_id']} status={summary['status']} "
        f"errors={summary['validation_error_count']} output={output}"
    )
    return 0 if summary["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
