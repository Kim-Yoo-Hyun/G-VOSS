#!/usr/bin/env python3
"""Audit whether H002 dry RGA-HL is equivalent to H001 Violation@K."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
KS = (50, 100)


SOURCES: dict[str, dict[str, Any]] = {
    "vlsat": {
        "source_id": "vlsat",
        "root": REPO_ROOT / "experiments/H001_geom_reliability/sources/vlsat/full_validation",
        "projection_summary": H002_ROOT / "artifacts/rga_smoke/vlsat_summary.json",
        "source_caveat": "controlled full-validation source",
    },
    "open3dsg_recovery_relaxed_views_min2": {
        "source_id": "open3dsg_recovery_relaxed_views_min2",
        "root": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2",
        "projection_summary": H002_ROOT / "artifacts/rga_smoke/open3dsg_recovery_summary.json",
        "source_caveat": (
            "recovery-policy variant; not unmodified Open3DSG preprocessing"
        ),
    },
}


CHECKABLE = {"satisfied", "uncertain", "violated"}
STATUS_TO_AXIS = {
    "satisfied": "H",
    "violated": "L",
    "uncertain": "U",
    "unsupported": "M",
}


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


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nested_get(row: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = row
    for part in path:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def family(row: dict[str, Any]) -> str:
    return str(nested_get(row, ("predicate", "predicate_family")))


def prediction_id(row: dict[str, Any]) -> str:
    return str(row["prediction_id"])


def subgraph_id(row: dict[str, Any]) -> str:
    return str(row["subgraph_id"])


def semantic_rank(row: dict[str, Any]) -> int | None:
    value = nested_get(row, ("semantic", "ranks", "semantic_rank_in_subgraph"))
    if value is None:
        value = nested_get(row, ("ranks", "semantic_rank_in_subgraph"))
    if value is None:
        return None
    return int(value)


def ranking_score(row: dict[str, Any]) -> float:
    value = nested_get(row, ("scores", "ranking_score"))
    if value is None:
        value = nested_get(row, ("semantic", "ranking_score"))
    return float(value)


def h001_sort_key(row: dict[str, Any]) -> tuple[float, int, int, str]:
    return (
        -ranking_score(row),
        int(nested_get(row, ("edge", "subject_id"))),
        int(nested_get(row, ("edge", "object_id"))),
        str(nested_get(row, ("predicate", "predicate_label"))),
    )


def status_for(row_or_verification: dict[str, Any]) -> str:
    return str(row_or_verification.get("verification_status"))


def selected_by_h001(predictions: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    scoped = [row for row in predictions if family(row) in DEFAULT_FAMILIES]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scoped:
        groups[subgraph_id(row)].append(row)
    selected: list[dict[str, Any]] = []
    for rows in groups.values():
        rows.sort(key=h001_sort_key)
        selected.extend(rows[:k])
    return selected


def selected_by_global_rank(geometry_rows: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    return [row for row in geometry_rows if (semantic_rank(row) or 10**9) <= k]


def selected_status_summary(
    rows: list[dict[str, Any]], verification_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    statuses: Counter[str] = Counter()
    families: Counter[str] = Counter()
    missing_verification = 0
    for row in rows:
        families[family(row)] += 1
        verification = verification_by_id.get(prediction_id(row))
        if verification is None:
            missing_verification += 1
            statuses["missing"] += 1
            continue
        statuses[status_for(verification)] += 1
    denom = sum(statuses.get(status, 0) for status in CHECKABLE)
    violated = statuses.get("violated", 0)
    return {
        "selected_rows": len(rows),
        "denominator": denom,
        "violated": violated,
        "violation_rate": violated / denom if denom else None,
        "status_counts": dict(sorted(statuses.items())),
        "family_counts": dict(sorted(families.items())),
        "missing_verification": missing_verification,
    }


def rga_hl_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(status_for(row) for row in rows)
    denom = sum(statuses.get(status, 0) for status in CHECKABLE)
    violated = statuses.get("violated", 0)
    covered = denom
    topk_rows = len(rows)
    return {
        "selected_rows": topk_rows,
        "covered_denominator": covered,
        "violated": violated,
        "rga_hl_at_k": violated / covered if covered else None,
        "status_counts": dict(sorted(statuses.items())),
        "family_counts": dict(sorted(Counter(family(row) for row in rows).items())),
        "coverage": covered / topk_rows if topk_rows else None,
    }


def compare_sets(global_rows: list[dict[str, Any]], h001_rows: list[dict[str, Any]]) -> dict[str, Any]:
    global_ids = {prediction_id(row) for row in global_rows}
    h001_ids = {prediction_id(row) for row in h001_rows}
    intersection = global_ids & h001_ids
    return {
        "global_rank_selected": len(global_ids),
        "h001_scoped_score_selected": len(h001_ids),
        "intersection": len(intersection),
        "global_only": len(global_ids - h001_ids),
        "h001_only": len(h001_ids - global_ids),
        "jaccard": len(intersection) / len(global_ids | h001_ids) if global_ids or h001_ids else None,
    }


def h001_metric_reference(metrics: dict[str, Any]) -> dict[str, Any]:
    by_k = (
        ((metrics.get("conditions") or {}).get("semantic_only") or {})
        .get("violation_rate", {})
        .get("by_k", {})
    )
    return {
        key: {
            "denominator": value.get("denominator"),
            "violated": value.get("violated"),
            "violation_rate": value.get("violation_rate"),
        }
        for key, value in sorted(by_k.items())
    }


def nearly_equal(a: Any, b: Any, eps: float = 1e-12) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= eps


def audit(config: dict[str, Any]) -> dict[str, Any]:
    root = config["root"]
    prediction_path = root / "adapter/predictions.jsonl"
    geometry_path = root / "geometry/verification.jsonl"
    metrics_path = root / "metrics/metrics.json"
    projection_summary_path = config["projection_summary"]

    predictions = [row for _, row in read_jsonl(prediction_path)]
    geometry_rows = [row for _, row in read_jsonl(geometry_path)]
    verification_by_id = {prediction_id(row): row for row in geometry_rows}
    metrics = load_json(metrics_path)
    projection_summary = load_json(projection_summary_path)
    h001_reference = h001_metric_reference(metrics)

    per_k: dict[str, Any] = {}
    equivalence_errors: list[str] = []
    for k in KS:
        global_rows = selected_by_global_rank(geometry_rows, k)
        h001_rows = selected_by_h001(predictions, k)
        h001_selected_summary = selected_status_summary(h001_rows, verification_by_id)
        global_summary = rga_hl_summary(global_rows)
        reference = h001_reference[str(k)]
        h001_equivalent = (
            h001_selected_summary["denominator"] == reference["denominator"]
            and h001_selected_summary["violated"] == reference["violated"]
            and nearly_equal(h001_selected_summary["violation_rate"], reference["violation_rate"])
        )
        if not h001_equivalent:
            equivalence_errors.append(f"k={k}:h001_selection_does_not_match_metric_reference")

        per_k[str(k)] = {
            "global_rank_rga": global_summary,
            "h001_scoped_score_selection": h001_selected_summary,
            "h001_metric_reference": reference,
            "h001_selection_matches_metric_reference": h001_equivalent,
            "selection_overlap": compare_sets(global_rows, h001_rows),
            "interpretation": (
                "H002 dry RGA uses global semantic_rank_in_subgraph, while H001 "
                "Violation@K filters to H001 families and re-sorts by ranking_score."
            ),
        }

    status = "equivalence_audit_ready" if not equivalence_errors else "blocked"
    return {
        "schema_version": "h002_rga_equivalence_audit_v0",
        "source_id": config["source_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "predictions": str(prediction_path.relative_to(REPO_ROOT)),
            "geometry": str(geometry_path.relative_to(REPO_ROOT)),
            "metrics": str(metrics_path.relative_to(REPO_ROOT)),
            "projection_summary": str(projection_summary_path.relative_to(REPO_ROOT)),
        },
        "projection_status": projection_summary.get("status"),
        "families": sorted(DEFAULT_FAMILIES),
        "per_k": per_k,
        "equivalence_errors": equivalence_errors,
        "source_caveat": config["source_caveat"],
        "status": status,
    }


def main() -> int:
    args = parse_args()
    config = SOURCES[args.source]
    result = audit(config)
    output = args.output
    if not output.is_absolute():
        output = H002_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        f"{result['source_id']} status={result['status']} "
        f"errors={len(result['equivalence_errors'])} output={output}"
    )
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
