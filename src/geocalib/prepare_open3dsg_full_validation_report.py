#!/usr/bin/env python3
"""Regenerate Open3DSG full-validation table/caveat artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_full_validation_report_v1"
TARGET_FAMILIES = ("support_contact", "proximity", "relative_vertical")
CONDITION_LABELS = {
    "semantic_only": "semantic_only",
    "probabilistic_recalibrated": "probabilistic_recalibrated",
    "rule_verified_point_subtype": "rule_verified_point_subtype",
    "control_family_specific_p_geom_valid": "family_specific_p_geom_valid",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/full_validation"),
    )
    parser.add_argument(
        "--vlsat-source-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/vlsat/full_validation"),
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/"
            "363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/"
            "epoch=13-step=13104.ckpt"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/full_validation/table_caveats"),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def count_lines(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def status_of(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "missing"
    return str(payload.get("status", "unknown"))


def metric_value(condition: dict[str, Any], block: str, k: int, name: str) -> float | None:
    value = condition.get(block, {}).get("by_k", {}).get(str(k), {}).get(name)
    return None if value is None else float(value)


def condition_summary(metrics: dict[str, Any] | None, condition_key: str) -> dict[str, Any] | None:
    if metrics is None:
        return None
    condition = metrics.get("conditions", {}).get(condition_key)
    if not isinstance(condition, dict):
        return None
    return {
        "condition": CONDITION_LABELS[condition_key],
        "R@50": metric_value(condition, "recall", 50, "recall"),
        "R@100": metric_value(condition, "recall", 100, "recall"),
        "Violation@50": metric_value(condition, "violation_rate", 50, "violation_rate"),
        "Violation@100": metric_value(condition, "violation_rate", 100, "violation_rate"),
        "selected@50": condition.get("recall", {}).get("by_k", {}).get("50", {}).get("selected_predictions"),
        "selected@100": condition.get("recall", {}).get("by_k", {}).get("100", {}).get("selected_predictions"),
    }


def h001_denominator(metrics: dict[str, Any] | None) -> int | None:
    if metrics is None:
        return None
    by_family = metrics.get("counts", {}).get("ground_truth_by_family", {})
    if not isinstance(by_family, dict):
        return None
    return sum(int(by_family.get(family, 0)) for family in TARGET_FAMILIES)


def coverage_summary(repo_root: Path, source_root: Path, vlsat_root: Path, checkpoint: Path) -> dict[str, Any]:
    payload = load_json(source_root / "payload/manifest.json")
    views = load_json(source_root / "views/manifest.json")
    preprocess = load_json(source_root / "preprocess/manifest.json")
    features = load_json(source_root / "features/manifest.json")
    raw_identity = load_json(source_root / "raw_dump_identity/manifest.json")
    adapter = load_json(source_root / "adapter/manifest.json")
    geometry = load_json(source_root / "geometry/manifest.json")
    metrics = load_json(source_root / "metrics/metrics.json")
    bootstrap = load_json(source_root / "bootstrap_ci/summary.json")
    failure_rows = source_root / "failure_rows/rows.jsonl"
    vlsat_metrics = load_json(vlsat_root / "metrics/metrics.json")

    feature_audit = features.get("selected_run_audit", {}) if isinstance(features, dict) else {}
    raw_dump = raw_identity.get("raw_dump", {}) if isinstance(raw_identity, dict) else {}
    return {
        "checkpoint": {
            "path": relpath(repo_root, checkpoint),
            "exists": checkpoint.is_file(),
            "route": "official_non_avg_blip_epoch13_step13104",
        },
        "payload": {
            "status": status_of(payload),
            "counts": payload.get("counts") if isinstance(payload, dict) else None,
        },
        "views": {
            "status": status_of(views),
            "summary": views.get("summary") if isinstance(views, dict) else None,
        },
        "preprocess": {
            "status": status_of(preprocess),
            "summary": preprocess.get("summary") if isinstance(preprocess, dict) else None,
            "warnings": preprocess.get("warnings") if isinstance(preprocess, dict) else None,
            "blockers": preprocess.get("blockers") if isinstance(preprocess, dict) else None,
        },
        "features": {
            "status": status_of(feature_audit if feature_audit else features),
            "run_dir": feature_audit.get("run_dir"),
            "complete_feature_ids": feature_audit.get("complete_all_roles_total"),
            "expected_feature_ids": feature_audit.get("expected_unique_total"),
            "missing_preprocessed": (
                feature_audit.get("split_coverage", {})
                .get("validation", {})
                .get("missing_preprocessed")
            ),
            "blockers": feature_audit.get("blockers"),
        },
        "raw_dump_identity": {
            "status": status_of(raw_identity),
            "scope": raw_identity.get("scope") if isinstance(raw_identity, dict) else None,
            "raw_dump": raw_dump,
        },
        "adapter": {
            "status": status_of(adapter),
            "counts": adapter.get("counts") if isinstance(adapter, dict) else None,
        },
        "geometry": {
            "status": status_of(geometry),
            "counts": geometry.get("counts") if isinstance(geometry, dict) else None,
        },
        "metrics": {
            "status": status_of(metrics),
            "counts": metrics.get("counts") if isinstance(metrics, dict) else None,
            "h001_family_denominator": h001_denominator(metrics),
        },
        "bootstrap_ci": {
            "status": status_of(bootstrap),
            "sources": sorted(bootstrap.get("sources", {}).keys()) if isinstance(bootstrap, dict) else [],
        },
        "failure_rows": {
            "path": relpath(repo_root, failure_rows),
            "rows": count_lines(failure_rows),
            "exists": failure_rows.is_file(),
        },
        "vlsat_full_validation_reference": {
            "status": status_of(vlsat_metrics),
            "counts": vlsat_metrics.get("counts") if isinstance(vlsat_metrics, dict) else None,
            "h001_family_denominator": h001_denominator(vlsat_metrics),
        },
    }


def build_caveats(coverage: dict[str, Any], source_root: Path) -> list[str]:
    caveats = [
        "Open3DSG full-validation outputs are stored under a separate source root and do not overwrite the existing avg-BLIP or non-avg hardened branches.",
        "The checkpoint route is official non-averaged BLIP selected by train-dev loss before full-validation source-result reporting.",
        "Open3DSG remains a source-output reliability evaluation and re-ranking case study; it is not a claim of full Open3DSG paper reproduction unless stated separately.",
        "Exact-label recall denominator is limited to support_contact, proximity, and relative_vertical H001 families.",
        "Residual calibration risk remains: geometry consistency scores can demote/retain predictions but do not prove semantic correctness for every unlabeled relation.",
    ]
    missing_pre = coverage["features"].get("missing_preprocessed")
    if missing_pre:
        caveats.append(
            f"Open3DSG full-validation feature coverage excludes {missing_pre} contexts without loadable preprocessed pickles; report this as a covered-context denominator caveat."
        )
    preprocess_summary = coverage["preprocess"].get("summary") or {}
    missing_contexts = preprocess_summary.get("missing_subgraph_count")
    if missing_contexts:
        caveats.append(
            f"Open3DSG preprocessing produced {missing_contexts} missing contexts after recovery attempts; these are treated as explicit source-runtime caveats."
        )
    if (source_root / "preprocess/recovery_generation_manifest.json").is_file() or (
        source_root / "views/recovery_relaxed_two_scan_manifest.json"
    ).is_file():
        caveats.append(
            "This recovery variant resolves the 15 missing contexts by relaxing the Open3DSG preprocess visible-object gate to min_visible=2 and regenerating relaxed views for two scans; report it as a recovery-policy variant, not as the unmodified source preprocess route."
        )
    return caveats


def render_report(payload: dict[str, Any]) -> str:
    table = payload["table6_candidate"]
    lines = [
        "# Open3DSG Full-Validation Table/Caveat Regeneration",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at_utc']}`",
        "",
        "## Coverage",
        "",
        f"- payload: `{payload['coverage']['payload']['status']}`",
        f"- views: `{payload['coverage']['views']['status']}`",
        f"- preprocess: `{payload['coverage']['preprocess']['status']}`",
        (
            f"- features: `{payload['coverage']['features']['complete_feature_ids']}/"
            f"{payload['coverage']['features']['expected_feature_ids']}` complete feature ids"
        ),
        f"- raw dump identity: `{payload['coverage']['raw_dump_identity']['status']}`",
        f"- adapter: `{payload['coverage']['adapter']['status']}`",
        f"- geometry: `{payload['coverage']['geometry']['status']}`",
        f"- metrics: `{payload['coverage']['metrics']['status']}`",
        f"- bootstrap CI: `{payload['coverage']['bootstrap_ci']['status']}`",
        f"- failure rows: `{payload['coverage']['failure_rows']['rows']}`",
        "",
        "## Table 6 Candidate",
        "",
        "| condition | R@50 | R@100 | V@50 | V@100 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in table:
        def fmt(value: Any) -> str:
            return "NA" if value is None else f"{float(value):.4f}"

        lines.append(
            f"| {row['condition']} | {fmt(row['R@50'])} | {fmt(row['R@100'])} | "
            f"{fmt(row['Violation@50'])} | {fmt(row['Violation@100'])} |"
        )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in payload["caveats"])
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    source_root = resolve(repo_root, args.source_root)
    vlsat_root = resolve(repo_root, args.vlsat_source_root)
    checkpoint = resolve(repo_root, args.checkpoint)
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics = load_json(source_root / "metrics/metrics.json")
    coverage = coverage_summary(repo_root, source_root, vlsat_root, checkpoint)
    table = [
        summary
        for key in CONDITION_LABELS
        if (summary := condition_summary(metrics, key)) is not None
    ]

    blockers: list[str] = []
    for stage in ("payload", "views", "adapter", "geometry", "metrics", "bootstrap_ci"):
        status = coverage[stage]["status"]
        if status not in {"ready", "views_ready"}:
            blockers.append(f"{stage}:{status}")
    if not table:
        blockers.append("table6_candidate:missing_metrics_conditions")
    if not coverage["failure_rows"]["exists"]:
        blockers.append("failure_rows:missing")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now(),
        "status": "open3dsg_full_validation_table_caveats_ready" if not blockers else "open3dsg_full_validation_table_caveats_blocked",
        "source_root": relpath(repo_root, source_root),
        "coverage": coverage,
        "table6_candidate": table,
        "caveats": build_caveats(coverage, source_root),
        "blockers": blockers,
        "claim_boundary": (
            "This artifact regenerates Open3DSG full-validation table/caveat wording. "
            "It does not by itself promote the route into the AAAI main claim."
        ),
    }

    write_json(out_dir / "manifest.json", payload)
    write_json(out_dir / "table6_candidate.json", table)
    (out_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
