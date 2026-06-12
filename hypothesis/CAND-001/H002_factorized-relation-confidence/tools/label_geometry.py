#!/usr/bin/env python3
"""Summarize label-geometry agreement from H001 failure rows for H002."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]


SOURCES = {
    "vlsat": {
        "source_id": "vlsat",
        "failure_rows": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl",
        "source_caveat": "controlled full-validation source",
    },
    "open3dsg_recovery_relaxed_views_min2": {
        "source_id": "open3dsg_recovery_relaxed_views_min2",
        "failure_rows": REPO_ROOT
        / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl",
        "source_caveat": (
            "recovery-policy variant; not unmodified Open3DSG preprocessing"
        ),
    },
}


SCOPES = ("all_failure_rows", "top50", "top100")
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


def scope_membership(row: dict[str, Any]) -> tuple[str, ...]:
    scopes = ["all_failure_rows"]
    topk = nested_get(row, ("source_prediction", "topk_membership"), {}) or {}
    if topk.get("top50"):
        scopes.append("top50")
    if topk.get("top100"):
        scopes.append("top100")
    return tuple(scopes)


def safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


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
        "gt_negative_geometry_satisfied": 0,
    }


def finalize_scope(scope: dict[str, Any]) -> dict[str, Any]:
    rows = scope["rows"]
    cross_tab = {
        label: dict(sorted(statuses.items()))
        for label, statuses in sorted(scope["cross_tab"].items())
    }
    exact_total = scope["exact_match_total"]
    label_positive_total = scope["label_positive_total"]
    return {
        "rows": rows,
        "cross_tab": cross_tab,
        "label_status_counts": dict(sorted(scope["label_status_counts"].items())),
        "geometry_status_counts": dict(sorted(scope["geometry_status_counts"].items())),
        "family_counts": dict(sorted(scope["family_counts"].items())),
        "target_counts": dict(sorted(scope["target_counts"].items())),
        "target_by_family": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(scope["target_by_family"].items())
        },
        "rates": {
            "exact_match_bad_geometry_rate": safe_rate(
                scope["exact_match_bad_geometry"], exact_total
            ),
            "label_positive_bad_geometry_rate": safe_rate(
                scope["label_positive_bad_geometry"], label_positive_total
            ),
            "gt_negative_geometry_satisfied_rate": safe_rate(
                scope["gt_negative_geometry_satisfied"],
                scope["label_status_counts"].get("no_gt_for_pair", 0)
                + scope["label_status_counts"].get("pair_has_other_predicate", 0),
            ),
        },
        "denominators": {
            "exact_match_total": exact_total,
            "label_positive_total": label_positive_total,
            "gt_negative_total": scope["label_status_counts"].get("no_gt_for_pair", 0)
            + scope["label_status_counts"].get("pair_has_other_predicate", 0),
        },
    }


def summarize(config: dict[str, Any]) -> dict[str, Any]:
    path = config["failure_rows"]
    scopes = {name: empty_scope() for name in SCOPES}
    validation_errors: list[str] = []
    examples: dict[str, list[dict[str, Any]]] = {f"{a}+{b}": [] for a, b in TARGET_KEYS}

    for line_no, row in read_jsonl(path):
        match_status = str(nested_get(row, ("ground_truth", "match_status"), "missing"))
        verification_status = str(nested_get(row, ("geometry", "verification_status"), "missing"))
        family = str(nested_get(row, ("source_prediction", "predicate_family"), "missing"))
        target_key = f"{match_status}+{verification_status}"

        if match_status == "missing":
            validation_errors.append(f"missing_match_status:line={line_no}")
        if verification_status == "missing":
            validation_errors.append(f"missing_verification_status:line={line_no}")

        for scope_name in scope_membership(row):
            scope = scopes[scope_name]
            scope["rows"] += 1
            scope["cross_tab"][match_status][verification_status] += 1
            scope["label_status_counts"][match_status] += 1
            scope["geometry_status_counts"][verification_status] += 1
            scope["family_counts"][family] += 1

            if (match_status, verification_status) in TARGET_KEYS:
                scope["target_counts"][target_key] += 1
                scope["target_by_family"][family][target_key] += 1

            if match_status == "exact_match":
                scope["exact_match_total"] += 1
                if verification_status in {"violated", "uncertain"}:
                    scope["exact_match_bad_geometry"] += 1
            if match_status in {"exact_match", "family_match"}:
                scope["label_positive_total"] += 1
                if verification_status in {"violated", "uncertain"}:
                    scope["label_positive_bad_geometry"] += 1
            if match_status in {"no_gt_for_pair", "pair_has_other_predicate"}:
                if verification_status == "satisfied":
                    scope["gt_negative_geometry_satisfied"] += 1

        if (match_status, verification_status) in TARGET_KEYS and len(examples[target_key]) < 10:
            examples[target_key].append(
                {
                    "line": line_no,
                    "prediction_id": nested_get(
                        row, ("source_prediction", "prediction_id"), "missing"
                    ),
                    "scan_id": nested_get(row, ("source_prediction", "scan_id"), "missing"),
                    "subgraph_id": nested_get(
                        row, ("source_prediction", "subgraph_id"), "missing"
                    ),
                    "predicate_family": family,
                    "predicate_label": nested_get(
                        row, ("source_prediction", "predicate_label"), "missing"
                    ),
                    "semantic_rank": nested_get(
                        row, ("source_prediction", "semantic_rank_in_subgraph"), None
                    ),
                    "topk_membership": nested_get(
                        row, ("source_prediction", "topk_membership"), {}
                    ),
                    "geometry_reason_codes": nested_get(
                        row, ("geometry", "reason_codes"), []
                    ),
                    "failure_category": nested_get(
                        row, ("failure_taxonomy", "primary_category"), "missing"
                    ),
                    "claim_use": nested_get(row, ("failure_taxonomy", "claim_use"), "missing"),
                }
            )

    status = "ready" if not validation_errors else "blocked"
    return {
        "schema_version": "h002_label_geometry_summary_v0",
        "source_id": config["source_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(path.relative_to(REPO_ROOT)),
        "source_caveat": config["source_caveat"],
        "scopes": {name: finalize_scope(scope) for name, scope in scopes.items()},
        "examples": examples,
        "validation_errors": validation_errors[:100],
        "validation_error_count": len(validation_errors),
        "status": status,
        "boundary": (
            "This diagnostic uses H001 failure_rows only. It is not all-row "
            "label-geometry agreement until a direct GT join is implemented."
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
