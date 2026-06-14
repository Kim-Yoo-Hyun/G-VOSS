#!/usr/bin/env python3
"""Validate H002 RGA projection feasibility without writing row-level outputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]


SOURCES: dict[str, dict[str, Any]] = {
    "vlsat": {
        "source_id": "vlsat",
        "scope_id": "full_official_validation",
        "root": REPO_ROOT / "experiments/H001_geom_reliability/sources/vlsat/full_validation",
        "expected": {
            "prediction_rows": 957_008,
            "geometry_rows": 957_008,
            "failure_rows": 59_841,
            "gt_rows": 11_254,
        },
        "source_caveat": "controlled full-validation source",
        "status_on_success": "ready_for_rga_diagnostic",
    },
    "open3dsg_recovery_relaxed_views_min2": {
        "source_id": "open3dsg_recovery_relaxed_views_min2",
        "scope_id": "full_official_validation_recovery",
        "root": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2",
        "expected": {
            "prediction_rows": 695_916,
            "geometry_rows": 695_916,
            "failure_rows": 82_155,
            "gt_rows": None,
        },
        "source_caveat": (
            "recovery-policy variant; not unmodified Open3DSG preprocessing"
        ),
        "status_on_success": "ready_for_rga_diagnostic_with_caveat",
    },
}


STATUS_TO_GEOM = {
    "satisfied": ("satisfied", "H"),
    "violated": ("unsatisfied", "L"),
    "uncertain": ("uncertain", "U"),
    "unsupported": ("unsupported", "M"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate H002 RGA projection feasibility from H001 artifacts."
    )
    parser.add_argument("--source", required=True, choices=sorted(SOURCES))
    parser.add_argument("--mode", default="validate-only", choices=["validate-only"])
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
                raise ValueError(f"{path}:{line_no}: invalid JSONL row: {exc}") from exc


def count_lines(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for count, _ in enumerate(handle, start=1):
            pass
    return count


def nested_get(row: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = row
    for part in path:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def semantic_rank(row: dict[str, Any]) -> Any:
    return nested_get(row, ("semantic", "ranks", "semantic_rank_in_subgraph")) or nested_get(
        row, ("ranks", "semantic_rank_in_subgraph")
    )


def source_score(row: dict[str, Any]) -> Any:
    value = nested_get(row, ("semantic", "ranking_score"))
    if value is not None:
        return value
    return nested_get(row, ("scores", "ranking_score"))


def required_field_errors(row: dict[str, Any]) -> list[str]:
    required = {
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "edge.subject_id": nested_get(row, ("edge", "subject_id")),
        "edge.object_id": nested_get(row, ("edge", "object_id")),
        "predicate.predicate_label": nested_get(row, ("predicate", "predicate_label")),
        "predicate.predicate_family": nested_get(row, ("predicate", "predicate_family")),
        "semantic_rank_in_subgraph": semantic_rank(row),
        "verification_status": row.get("verification_status"),
    }
    return [field for field, value in required.items() if value is None]


def rga_bucket(rank: Any, geom_axis: str, k: int) -> str:
    try:
        rank_int = int(rank)
    except (TypeError, ValueError):
        semantic_axis = "L"
    else:
        semantic_axis = "H" if rank_int <= k else "L"
    return f"RGA-{semantic_axis}{geom_axis}"


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dry_metrics(bucket_counts: Counter[str], k: int) -> dict[str, Any]:
    hh = bucket_counts.get(f"RGA-HH", 0)
    hl = bucket_counts.get(f"RGA-HL", 0)
    hu = bucket_counts.get(f"RGA-HU", 0)
    hm = bucket_counts.get(f"RGA-HM", 0)
    covered = hh + hl + hu
    topk = hh + hl + hu + hm
    return {
        "k": k,
        "covered_topk_denominator": covered,
        "topk_rows": topk,
        "rga_hl_at_k": hl / covered if covered else None,
        "rga_valid_at_k": hh / covered if covered else None,
        "rga_uncertain_at_k": hu / covered if covered else None,
        "rga_coverage_at_k": covered / topk if topk else None,
    }


def load_prediction_ids(path: Path) -> tuple[set[str], Counter[str], list[str]]:
    ids: set[str] = set()
    duplicate_ids: Counter[str] = Counter()
    missing_examples: list[str] = []
    for line_no, row in read_jsonl(path):
        prediction_id = row.get("prediction_id")
        if prediction_id is None:
            if len(missing_examples) < 20:
                missing_examples.append(f"line:{line_no}")
            continue
        if prediction_id in ids:
            duplicate_ids[prediction_id] += 1
        ids.add(prediction_id)
    return ids, duplicate_ids, missing_examples


def load_failure_status(path: Path) -> tuple[Counter[str], set[str]]:
    counts: Counter[str] = Counter()
    ids: set[str] = set()
    for _, row in read_jsonl(path):
        source_prediction = row.get("source_prediction") or {}
        prediction_id = source_prediction.get("prediction_id")
        if prediction_id:
            ids.add(prediction_id)
        status = nested_get(row, ("ground_truth", "match_status")) or "missing"
        counts[status] += 1
    return counts, ids


def load_h001_semantic_metrics(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)
    semantic = (metrics.get("conditions") or {}).get("semantic_only") or {}
    violation = semantic.get("violation_rate") or {}
    by_k = violation.get("by_k") or {}
    result: dict[str, Any] = {}
    for key in ("50", "100"):
        row = by_k.get(key) or {}
        result[key] = {
            "denominator": row.get("denominator"),
            "violated": row.get("violated"),
            "violation_rate": row.get("violation_rate"),
        }
    return result


def validate_source(config: dict[str, Any], mode: str) -> dict[str, Any]:
    root = config["root"]
    paths = {
        "prediction": root / "adapter/predictions.jsonl",
        "geometry": root / "geometry/verification.jsonl",
        "failure_rows": root / "failure_rows/rows.jsonl",
        "metrics": root / "metrics/metrics.json",
    }
    if config["expected"].get("gt_rows") is not None:
        paths["gt"] = root / "adapter/ground_truth.jsonl"

    validation_errors: list[str] = []
    warnings: list[str] = []
    for name, path in paths.items():
        if not path.is_file() or path.stat().st_size == 0:
            validation_errors.append(f"missing_or_empty_input:{name}:{path}")

    if validation_errors:
        return {
            "schema_version": "h002_rga_projection_summary_v0",
            "source_id": config["source_id"],
            "scope_id": config["scope_id"],
            "mode": mode,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "input_paths": {name: str(path.relative_to(REPO_ROOT)) for name, path in paths.items()},
            "validation_errors": validation_errors,
            "status": "blocked",
        }

    input_counts = {
        "prediction_rows": count_lines(paths["prediction"]),
        "geometry_rows": count_lines(paths["geometry"]),
        "failure_rows": count_lines(paths["failure_rows"]),
    }
    if "gt" in paths:
        input_counts["gt_rows"] = count_lines(paths["gt"])

    for key, expected_value in config["expected"].items():
        if expected_value is None:
            continue
        actual_value = input_counts.get(key)
        if actual_value != expected_value:
            validation_errors.append(
                f"unexpected_count:{key}:expected={expected_value}:actual={actual_value}"
            )

    prediction_ids, duplicate_predictions, missing_prediction_ids = load_prediction_ids(
        paths["prediction"]
    )

    geometry_ids: set[str] = set()
    duplicate_geometry: Counter[str] = Counter()
    missing_geometry_ids: list[str] = []
    required_field_missing_count = 0
    required_field_missing_examples: list[dict[str, Any]] = []
    unknown_status_count = 0
    unknown_status_examples: list[dict[str, Any]] = []
    geometry_status_counts: Counter[str] = Counter()
    h001_status_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    family_status_counts: dict[str, Counter[str]] = {}
    rga_top50: Counter[str] = Counter()
    rga_top100: Counter[str] = Counter()
    source_score_missing = 0
    p_geom_valid_available = 0
    p_geom_valid_missing = 0

    for line_no, row in read_jsonl(paths["geometry"]):
        prediction_id = row.get("prediction_id")
        if prediction_id is None:
            if len(missing_geometry_ids) < 20:
                missing_geometry_ids.append(f"line:{line_no}")
        else:
            if prediction_id in geometry_ids:
                duplicate_geometry[prediction_id] += 1
            geometry_ids.add(prediction_id)

        missing_fields = required_field_errors(row)
        if missing_fields:
            required_field_missing_count += 1
            if len(required_field_missing_examples) < 20:
                required_field_missing_examples.append(
                    {
                        "line": line_no,
                        "prediction_id": prediction_id,
                        "missing_fields": missing_fields,
                    }
                )

        h001_status = row.get("verification_status")
        h001_status_counts[str(h001_status)] += 1
        mapped = STATUS_TO_GEOM.get(str(h001_status))
        if mapped is None:
            unknown_status_count += 1
            geometry_status = "missing"
            geom_axis = "M"
            if len(unknown_status_examples) < 20:
                unknown_status_examples.append(
                    {"line": line_no, "prediction_id": prediction_id, "status": h001_status}
                )
        else:
            geometry_status, geom_axis = mapped
        geometry_status_counts[geometry_status] += 1

        family = nested_get(row, ("predicate", "predicate_family")) or "missing"
        family_counts[family] += 1
        family_status_counts.setdefault(family, Counter())[geometry_status] += 1

        rank = semantic_rank(row)
        rga_top50[rga_bucket(rank, geom_axis, 50)] += 1
        rga_top100[rga_bucket(rank, geom_axis, 100)] += 1

        if source_score(row) is None:
            source_score_missing += 1
        if finite_float(nested_get(row, ("calibration", "p_geom_valid"))) is None:
            p_geom_valid_missing += 1
        else:
            p_geom_valid_available += 1

    prediction_only = prediction_ids - geometry_ids
    geometry_only = geometry_ids - prediction_ids
    if prediction_only or geometry_only:
        validation_errors.append(
            f"prediction_geometry_key_mismatch:prediction_only={len(prediction_only)}:"
            f"geometry_only={len(geometry_only)}"
        )
    if duplicate_predictions:
        validation_errors.append(f"duplicate_prediction_ids:{sum(duplicate_predictions.values())}")
    if duplicate_geometry:
        validation_errors.append(f"duplicate_geometry_ids:{sum(duplicate_geometry.values())}")
    if missing_prediction_ids:
        validation_errors.append(f"missing_prediction_id_rows:{len(missing_prediction_ids)}")
    if missing_geometry_ids:
        validation_errors.append(f"missing_geometry_prediction_id_rows:{len(missing_geometry_ids)}")
    if required_field_missing_count:
        validation_errors.append(f"required_field_missing_rows:{required_field_missing_count}")
    if unknown_status_count:
        validation_errors.append(f"unknown_verification_status_rows:{unknown_status_count}")

    projected_rows = input_counts["geometry_rows"]
    if sum(rga_top50.values()) != projected_rows:
        validation_errors.append("rga_top50_counts_do_not_sum_to_projected_rows")
    if sum(rga_top100.values()) != projected_rows:
        validation_errors.append("rga_top100_counts_do_not_sum_to_projected_rows")

    failure_status_counts, failure_prediction_ids = load_failure_status(paths["failure_rows"])
    h001_semantic_metrics = load_h001_semantic_metrics(paths["metrics"])

    if source_score_missing:
        warnings.append(f"source_score_missing_rows:{source_score_missing}")
    if p_geom_valid_missing:
        warnings.append(f"p_geom_valid_missing_rows:{p_geom_valid_missing}")
    if config["source_id"].startswith("open3dsg") and "recovery" not in config["source_caveat"]:
        validation_errors.append("missing_open3dsg_recovery_caveat")

    posterior_non_null_count = 0
    if posterior_non_null_count:
        validation_errors.append(f"posterior_non_null_count:{posterior_non_null_count}")

    status = config["status_on_success"] if not validation_errors else "blocked"

    return {
        "schema_version": "h002_rga_projection_summary_v0",
        "source_id": config["source_id"],
        "scope_id": config["scope_id"],
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {name: str(path.relative_to(REPO_ROOT)) for name, path in paths.items()},
        "input_counts": input_counts,
        "expected_counts": config["expected"],
        "projected_counts": {
            "projected_rows": projected_rows,
            "row_level_artifact_created": False,
        },
        "key_parity": {
            "prediction_unique_ids": len(prediction_ids),
            "geometry_unique_ids": len(geometry_ids),
            "prediction_only_count": len(prediction_only),
            "geometry_only_count": len(geometry_only),
            "prediction_only_examples": sorted(prediction_only)[:20],
            "geometry_only_examples": sorted(geometry_only)[:20],
            "duplicate_prediction_id_count": sum(duplicate_predictions.values()),
            "duplicate_geometry_id_count": sum(duplicate_geometry.values()),
        },
        "required_field_check": {
            "missing_required_field_rows": required_field_missing_count,
            "examples": required_field_missing_examples,
        },
        "geometry_status_counts": dict(sorted(geometry_status_counts.items())),
        "h001_verification_status_counts": dict(sorted(h001_status_counts.items())),
        "predicate_family_counts": dict(sorted(family_counts.items())),
        "predicate_family_geometry_status_counts": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(family_status_counts.items())
        },
        "rga_bucket_top50_counts": dict(sorted(rga_top50.items())),
        "rga_bucket_top100_counts": dict(sorted(rga_top100.items())),
        "rga_metric_dry": {
            "50": dry_metrics(rga_top50, 50),
            "100": dry_metrics(rga_top100, 100),
            "definition": (
                "Dry RGA buckets use semantic_rank_in_subgraph and deterministic "
                "verification_status only; p_geom_valid thresholds are not used."
            ),
        },
        "h001_semantic_only_violation": h001_semantic_metrics,
        "failure_row_label_status_counts": dict(sorted(failure_status_counts.items())),
        "failure_row_prediction_id_count": len(failure_prediction_ids),
        "label_coverage_boundary": (
            "Failure rows provide partial top-K/failure label evidence only; all-row "
            "label-geometry buckets require a direct GT join."
        ),
        "posterior_guard": {
            "posterior_non_null_count": posterior_non_null_count,
            "posterior_edge_valid_policy": "null_until_factor_graph_defined",
            "p_geom_valid_copied_to_posterior": False,
        },
        "score_availability": {
            "source_score_missing_rows": source_score_missing,
            "p_geom_valid_available_rows": p_geom_valid_available,
            "p_geom_valid_missing_rows": p_geom_valid_missing,
        },
        "provenance_caveats": [config["source_caveat"]],
        "warnings": warnings,
        "validation_errors": validation_errors,
        "status": status,
    }


def main() -> int:
    args = parse_args()
    config = SOURCES[args.source]
    summary = validate_source(config, args.mode)

    output = args.output
    if not output.is_absolute():
        output = H002_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(
        f"{summary['source_id']} status={summary['status']} "
        f"errors={len(summary.get('validation_errors', []))} output={output}"
    )
    return 0 if summary["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
