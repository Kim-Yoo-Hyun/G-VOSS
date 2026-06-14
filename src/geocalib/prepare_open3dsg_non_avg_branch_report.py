#!/usr/bin/env python3
"""Build the Open3DSG non-avg branch Table 6/caveat comparison artifact."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_non_avg_branch_report_v1"
STATUS_READY = "open3dsg_non_avg_branch_ready"
STATUS_BLOCKED = "blocked_missing_non_avg_downstream_metrics"


CONDITIONS = (
    "semantic_only",
    "probabilistic_recalibrated",
    "rule_verified_point_subtype",
    "control_family_specific_p_geom_valid",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/non_avg/table6_caveats"),
    )
    parser.add_argument(
        "--avg-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg"),
    )
    parser.add_argument(
        "--non-avg-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/non_avg"),
    )
    parser.add_argument(
        "--checkpoint-selection",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/manifest.json"),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_optional_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f"missing:{path}"
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), None
    except Exception as exc:  # noqa: BLE001 - report must capture unreadable artifacts.
        return None, f"unreadable:{path}:{exc}"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def condition_summary(metrics: dict[str, Any] | None, condition: str) -> dict[str, Any] | None:
    if metrics is None:
        return None
    payload = metrics.get("conditions", {}).get(condition)
    if not payload:
        return None
    recall = payload.get("recall", {}).get("by_k", {})
    violation = payload.get("violation_rate", {}).get("by_k", {})
    return {
        "r50": recall.get("50", {}).get("recall"),
        "r100": recall.get("100", {}).get("recall"),
        "violation50": violation.get("50", {}).get("violation_rate"),
        "violation100": violation.get("100", {}).get("violation_rate"),
    }


def delta(new: dict[str, Any] | None, old: dict[str, Any] | None) -> dict[str, Any] | None:
    if new is None or old is None:
        return None
    out: dict[str, Any] = {}
    for key in ("r50", "r100", "violation50", "violation100"):
        if new.get(key) is None or old.get(key) is None:
            out[key] = None
        else:
            out[key] = float(new[key]) - float(old[key])
    return out


def build_payload(repo_root: Path, avg_root: Path, non_avg_root: Path, checkpoint_path: Path, out_dir: Path) -> dict[str, Any]:
    avg_metrics, avg_error = load_optional_json(avg_root / "metrics/metrics.json")
    non_avg_metrics, non_avg_error = load_optional_json(non_avg_root / "metrics/metrics.json")
    non_avg_raw_identity, raw_identity_error = load_optional_json(non_avg_root / "raw_dump_identity/manifest.json")
    non_avg_adapter, adapter_error = load_optional_json(non_avg_root / "adapter/manifest.json")
    non_avg_geometry, geometry_error = load_optional_json(non_avg_root / "geometry/manifest.json")
    non_avg_bootstrap, bootstrap_error = load_optional_json(non_avg_root / "bootstrap_ci/summary.json")
    checkpoint, checkpoint_error = load_optional_json(checkpoint_path)

    blocked: list[str] = []
    warnings: list[str] = []
    if avg_metrics is None or avg_metrics.get("status") != "ready":
        blocked.append(f"avg_metrics_not_ready:{avg_error or avg_metrics.get('status') if avg_metrics else avg_error}")
    if non_avg_metrics is None or non_avg_metrics.get("status") != "ready":
        blocked.append(f"non_avg_metrics_not_ready:{non_avg_error or non_avg_metrics.get('status') if non_avg_metrics else non_avg_error}")
    if checkpoint is None:
        blocked.append(f"checkpoint_selection_missing:{checkpoint_error}")
    elif checkpoint.get("status") != "checkpoint_selection_ready_official_non_avg_blip":
        blocked.append(f"checkpoint_selection_not_non_avg_ready:{checkpoint.get('status')}")

    for name, payload, error in (
        ("raw_identity", non_avg_raw_identity, raw_identity_error),
        ("adapter", non_avg_adapter, adapter_error),
        ("geometry", non_avg_geometry, geometry_error),
        ("bootstrap", non_avg_bootstrap, bootstrap_error),
    ):
        if payload is None:
            warnings.append(f"{name}_missing:{error}")

    avg_conditions = {condition: condition_summary(avg_metrics, condition) for condition in CONDITIONS}
    non_avg_conditions = {
        condition: condition_summary(non_avg_metrics, condition) for condition in CONDITIONS
    }
    deltas = {
        condition: delta(non_avg_conditions.get(condition), avg_conditions.get(condition))
        for condition in CONDITIONS
    }

    status = STATUS_READY if not blocked else STATUS_BLOCKED
    route_comparison = checkpoint.get("route_comparison", {}) if checkpoint else {}
    caveat_wording = {
        "if_blocked": (
            "Do not update the current paper Table 6 or Open3DSG caveat wording. "
            "The active downstream result remains the avg-BLIP Open3DSG branch."
        ),
        "if_ready": (
            "Report the official non-avg Open3DSG branch as a separately regenerated downstream result. "
            "The averaged-BLIP caveat can be removed only for this branch, while filtered train/dev, "
            "covered H001 377/388, exact-label denominator 2545, validation_missing_preprocessed:11, "
            "and residual calibration-risk caveats remain visible. Promotion over avg-BLIP requires user confirmation."
        ),
    }
    table6_rows = [
        {
            "prediction_source": "Open3DSG avg-BLIP",
            "artifact": relpath(repo_root, avg_root / "metrics/metrics.json"),
            "metric_status": avg_metrics.get("status") if avg_metrics else "missing",
            "claim_use": "current paper-facing Open3DSG result",
            "caveat_note": "averaged-BLIP variant; filtered train/dev; covered H001 377/388; exact-label denominator 2545",
        },
        {
            "prediction_source": "Open3DSG official non-avg",
            "artifact": relpath(repo_root, non_avg_root / "metrics/metrics.json"),
            "metric_status": non_avg_metrics.get("status") if non_avg_metrics else "missing",
            "claim_use": "candidate replacement or robustness branch after full downstream regeneration",
            "caveat_note": "official non-avg checkpoint; filtered train/dev and covered-scope caveats still apply",
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "blocked": blocked,
        "warnings": warnings,
        "inputs": {
            "avg_root": relpath(repo_root, avg_root),
            "non_avg_root": relpath(repo_root, non_avg_root),
            "checkpoint_selection": relpath(repo_root, checkpoint_path),
        },
        "route_comparison": route_comparison,
        "conditions": {
            "avg_blip": avg_conditions,
            "official_non_avg": non_avg_conditions,
            "non_avg_minus_avg": deltas,
        },
        "table6_rows": table6_rows,
        "caveat_wording": caveat_wording,
        "outputs": {
            "manifest_json": relpath(repo_root, out_dir / "manifest.json"),
            "report_md": relpath(repo_root, out_dir / "report.md"),
            "table_json": relpath(repo_root, out_dir / "table6_non_avg_comparison.json"),
        },
        "claim_boundary": (
            "This artifact compares Open3DSG downstream branches. It does not promote the non-avg branch "
            "to the main paper claim without complete metrics, bootstrap, caveat wording, and user confirmation."
        ),
    }


def fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Non-Avg Branch Table 6 And Caveat Report",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Branch Status",
        "",
    ]
    if payload["blocked"]:
        lines.extend(f"- blocker: `{item}`" for item in payload["blocked"])
    else:
        lines.append("- blockers: none")
    if payload["warnings"]:
        lines.extend(f"- warning: `{item}`" for item in payload["warnings"])
    lines.extend(["", "## Table 6 Candidate Rows", ""])
    lines.append("| source | metric status | claim use | caveat |")
    lines.append("| --- | --- | --- | --- |")
    for row in payload["table6_rows"]:
        lines.append(
            f"| {row['prediction_source']} | {row['metric_status']} | {row['claim_use']} | {row['caveat_note']} |"
        )
    lines.extend(["", "## Metric Comparison", ""])
    lines.append("| condition | avg R@100 | non-avg R@100 | delta R@100 | avg V@100 | non-avg V@100 | delta V@100 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for condition in CONDITIONS:
        avg = payload["conditions"]["avg_blip"].get(condition) or {}
        non = payload["conditions"]["official_non_avg"].get(condition) or {}
        diff = payload["conditions"]["non_avg_minus_avg"].get(condition) or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    condition,
                    fmt(avg.get("r100")),
                    fmt(non.get("r100")),
                    fmt(diff.get("r100")),
                    fmt(avg.get("violation100")),
                    fmt(non.get("violation100")),
                    fmt(diff.get("violation100")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Caveat Wording",
            "",
            f"- if blocked: {payload['caveat_wording']['if_blocked']}",
            f"- if ready: {payload['caveat_wording']['if_ready']}",
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    avg_root = resolve(repo_root, args.avg_root).resolve()
    non_avg_root = resolve(repo_root, args.non_avg_root).resolve()
    checkpoint_path = resolve(repo_root, args.checkpoint_selection).resolve()
    out_dir = resolve(repo_root, args.out).resolve()

    payload = build_payload(repo_root, avg_root, non_avg_root, checkpoint_path, out_dir)
    write_json(out_dir / "manifest.json", payload)
    write_json(out_dir / "table6_non_avg_comparison.json", payload["table6_rows"])
    (out_dir / "report.md").write_text(build_report(payload), encoding="utf-8")
    print(
        json.dumps(
            {"status": payload["status"], "blocked": payload["blocked"], "out": relpath(repo_root, out_dir)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
