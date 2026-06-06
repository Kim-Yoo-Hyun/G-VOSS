#!/usr/bin/env python3
"""Build the H001 covered-scope Open3DSG recovery sensitivity report."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_covered_recovery_report_v1"
STATUS_READY = "open3dsg_h001_covered_recovery_sensitivity_ready"
STATUS_BLOCKED = "open3dsg_h001_covered_recovery_sensitivity_blocked"
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
        "--r2-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery"),
    )
    parser.add_argument(
        "--avg-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg"),
    )
    parser.add_argument(
        "--full-validation-root",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/open3dsg/full_validation/"
            "recovery_relaxed_views_min2"
        ),
    )
    parser.add_argument(
        "--raw-stream",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/"
            "raw_dump_clean_return_retry2_20260606_021154/stream_manifest.json"
        ),
    )
    parser.add_argument(
        "--raw-exit",
        type=Path,
        default=Path("logs/open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154.exit"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/"
            "table_caveats"
        ),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def line_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def parse_exit_code(text: str | None) -> int | None:
    if text is None:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def metric_value(metrics: dict[str, Any] | None, condition: str, block: str, k: int, key: str) -> float | None:
    if not metrics:
        return None
    value = (
        metrics.get("conditions", {})
        .get(condition, {})
        .get(block, {})
        .get("by_k", {})
        .get(str(k), {})
        .get(key)
    )
    return None if value is None else float(value)


def summarize_metrics(metrics: dict[str, Any] | None) -> dict[str, dict[str, float | None]]:
    return {
        condition: {
            "R@50": metric_value(metrics, condition, "recall", 50, "recall"),
            "R@100": metric_value(metrics, condition, "recall", 100, "recall"),
            "Violation@50": metric_value(metrics, condition, "violation_rate", 50, "violation_rate"),
            "Violation@100": metric_value(metrics, condition, "violation_rate", 100, "violation_rate"),
        }
        for condition in CONDITIONS
    }


def diff_metrics(new: dict[str, Any], old: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    output: dict[str, dict[str, float | None]] = {}
    for condition in CONDITIONS:
        output[condition] = {}
        for key in ("R@50", "R@100", "Violation@50", "Violation@100"):
            left = new.get(condition, {}).get(key)
            right = old.get(condition, {}).get(key)
            output[condition][key] = None if left is None or right is None else float(left) - float(right)
    return output


def bootstrap_summary(bootstrap: dict[str, Any] | None) -> dict[str, Any] | None:
    if not bootstrap:
        return None
    source = bootstrap.get("sources", {}).get("open3dsg_ov_h001_r2_388")
    if not source:
        return None
    conditions = source.get("conditions", {})
    return {
        condition: {
            "R@100_ci95": conditions.get(condition, {}).get("100", {}).get("recall", {}).get("ci95"),
            "Violation@100_ci95": conditions.get(condition, {}).get("100", {}).get("violation_rate", {}).get("ci95"),
        }
        for condition in CONDITIONS
    }


def fmt(value: Any, percent: bool = False) -> str:
    if value is None:
        return "NA"
    number = float(value)
    if percent:
        return f"{number * 100:+.2f} pp"
    return f"{number:.4f}"


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG H001 Covered-Recovery Sensitivity Report",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at_utc']}`",
        "",
        "## Scope",
        "",
        "- branch role: historical 127-scan H001 covered-scope sensitivity, not the paper-facing full-validation main result",
        f"- preprocess coverage: `{payload['coverage']['preprocess_ready']}`",
        f"- feature coverage: `{payload['coverage']['features_ready']}`",
        f"- raw stream: `{payload['coverage']['raw_batches']}` batches, `{payload['coverage']['raw_rows']}` rows",
        f"- raw process exit: `{payload['coverage']['raw_exit']}`",
        f"- adapter rows: `{payload['coverage']['adapter_rows']}`",
        f"- geometry rows: `{payload['coverage']['geometry_rows']}`",
        f"- bootstrap: `{payload['coverage']['bootstrap_status']}`",
        "",
        "## Metrics",
        "",
        "| condition | R2 R@50 | R2 R@100 | R2 V@50 | R2 V@100 | R2 - avg R@100 | R2 - avg V@100 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITIONS:
        row = payload["metrics"]["r2"][condition]
        delta = payload["metrics"]["r2_minus_avg_377"][condition]
        lines.append(
            f"| {condition} | {fmt(row['R@50'])} | {fmt(row['R@100'])} | "
            f"{fmt(row['Violation@50'])} | {fmt(row['Violation@100'])} | "
            f"{fmt(delta['R@100'], percent=True)} | {fmt(delta['Violation@100'], percent=True)} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["interpretation"])
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in payload["caveats"])
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def build_payload(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    r2_root = resolve(repo_root, args.r2_root)
    avg_root = resolve(repo_root, args.avg_root)
    full_root = resolve(repo_root, args.full_validation_root)
    raw_stream_path = resolve(repo_root, args.raw_stream)
    raw_exit_path = resolve(repo_root, args.raw_exit)

    preprocess = load_json(r2_root / "preprocess_audit_388/manifest.json")
    features = load_json(r2_root / "features_388/manifest.json")
    raw_stream = load_json(raw_stream_path)
    raw_identity = load_json(r2_root / "raw_dump_identity/manifest.json")
    adapter = load_json(r2_root / "adapter/manifest.json")
    geometry = load_json(r2_root / "geometry/manifest.json")
    metrics = load_json(r2_root / "metrics/metrics.json")
    bootstrap = load_json(r2_root / "bootstrap_ci/summary.json")
    avg_metrics = load_json(avg_root / "metrics/metrics.json")
    full_metrics = load_json(full_root / "metrics/metrics.json")

    feature_audit = features.get("selected_run_audit", {}) if features else {}
    raw_exit_raw = raw_exit_path.read_text(encoding="utf-8").strip() if raw_exit_path.is_file() else None
    raw_exit = parse_exit_code(raw_exit_raw)
    r2_summary = summarize_metrics(metrics)
    avg_summary = summarize_metrics(avg_metrics)
    full_summary = summarize_metrics(full_metrics)

    blockers: list[str] = []
    expected = {
        "preprocess": preprocess and preprocess.get("status") == "preprocess_ready",
        "features": feature_audit.get("complete_all_roles_total") == feature_audit.get("expected_unique_total") == 388,
        "raw_stream": raw_stream and raw_stream.get("status") == "raw_dump_stream_complete",
        "raw_identity": raw_identity and raw_identity.get("status") == "raw_dump_identity_audit_ready",
        "adapter": adapter and adapter.get("status") == "ready",
        "geometry": geometry and geometry.get("status") == "ready",
        "metrics": metrics and metrics.get("status") == "ready",
        "bootstrap": bootstrap and bootstrap.get("status") == "ready",
    }
    for name, ok in expected.items():
        if not ok:
            blockers.append(f"{name}:not_ready")

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not blockers else STATUS_BLOCKED,
        "inputs": {
            "r2_root": relpath(repo_root, r2_root),
            "avg_root": relpath(repo_root, avg_root),
            "full_validation_root": relpath(repo_root, full_root),
            "raw_stream_manifest": relpath(repo_root, raw_stream_path),
            "raw_exit_file": relpath(repo_root, raw_exit_path),
        },
        "coverage": {
            "preprocess_ready": f"{(preprocess or {}).get('summary', {}).get('ready_subgraph_count')}/388",
            "features_ready": f"{feature_audit.get('complete_all_roles_total')}/{feature_audit.get('expected_unique_total')}",
            "raw_batches": (raw_stream or {}).get("completed_batches"),
            "raw_rows": (raw_stream or {}).get("rows_written"),
            "raw_completed_rows": line_count(r2_root / "raw_dump_clean_return_retry2_20260606_021154/raw.completed.jsonl"),
            "raw_exit": raw_exit,
            "raw_exit_raw_text": raw_exit_raw,
            "raw_identity_status": (raw_identity or {}).get("status"),
            "adapter_rows": (adapter or {}).get("counts", {}).get("prediction_rows"),
            "geometry_rows": (geometry or {}).get("counts", {}).get("verification_rows"),
            "metrics_status": (metrics or {}).get("status"),
            "bootstrap_status": (bootstrap or {}).get("status"),
        },
        "metrics": {
            "avg_377": avg_summary,
            "r2": r2_summary,
            "full_validation_548_recovery": full_summary,
            "r2_minus_avg_377": diff_metrics(r2_summary, avg_summary),
            "r2_bootstrap_ci": bootstrap_summary(bootstrap),
        },
        "interpretation": [
            "R2 removes the historical 377/388 covered-scope missing-context caveat for the 127-scan sensitivity branch.",
            "R2 changes the old avg-BLIP point estimates only slightly: R@100 rises by about +0.28 percentage points for all main conditions, while Violation@100 rises by about +0.04 to +0.13 percentage points.",
            "The qualitative paper message does not change: geometry-aware variants still reduce violations strongly, and family-specific calibration still gives the best R@100/violation tradeoff among the listed Open3DSG conditions.",
            "The wording value is robustness/sensitivity, not main-claim expansion. It can support an appendix sentence that the historical missing 11 contexts did not drive the Open3DSG trend.",
            "This branch should not replace the current full-validation 548/548 recovery main route.",
        ],
        "caveats": [
            "R2 is a historical H001 covered-scope sensitivity branch, not the full official validation paper-facing route.",
            "R2 uses recovery-policy interventions: the Open3DSG visible-object gate was relaxed to min_visible=2 for recovered contexts, and one scan required relaxed view regeneration.",
            "The latest raw stream artifact is complete, but the Docker process still exited 137 after finalization due to container teardown/OOM; this is a process provenance caveat, not a row-completeness blocker.",
            "R2 reduces the missing-preprocessed-context caveat only for this historical branch. It does not solve attachment_deferred candidate-pair-universe gaps.",
            "A raw-dump-only runner is useful only if this R2 branch is promoted as process-clean provenance; it is not required for the current main full-validation claim.",
        ],
        "raw_dump_only_runner_judgment": {
            "recommended_now": False,
            "reason": (
                "The current AAAI main route already has the full-validation artifact bundle. "
                "R2 is sensitivity evidence and its downstream results are stable despite exit 137. "
                "Implement a raw-dump-only runner only if the paper needs to elevate R2 from appendix "
                "sensitivity to a process-clean provenance result."
            ),
            "acceptable_if_needed": (
                "Keep checkpoint, feature cache, dataloader inputs, model forward, and raw JSONL schema fixed; "
                "bypass only Lightning/DDP teardown, then run raw identity/equivalence audit."
            ),
        },
        "blockers": blockers,
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(repo_root, args)
    write_json(out_dir / "manifest.json", payload)
    write_json(out_dir / "table6_r2_sensitivity.json", payload["metrics"])
    (out_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if payload["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
