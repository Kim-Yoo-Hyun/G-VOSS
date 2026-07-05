#!/usr/bin/env python3
"""Review support/contact hard-route metric runner outputs after train/eval alignment."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_support_contact_harder_route_metric_runner_after_train_eval_alignment_v1"
STATUS_READY = "h002_support_contact_harder_route_metric_runner_after_train_eval_alignment_ready"
STATUS_ERRORS = "h002_support_contact_harder_route_metric_runner_after_train_eval_alignment_input_errors"
EXPECTED_RUNTIME_STATUS = "h002_support_contact_harder_metric_runner_ready"
EXPECTED_RUNTIME_NEXT = "compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner"
EXPECTED_ALIGNMENT_STATUS = "h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_ready"
EXPECTED_PROTOCOL_STATUS = "h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--runtime-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest"),
    )
    parser.add_argument(
        "--alignment-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze"
        ),
    )
    parser.add_argument(
        "--protocol-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit"
        ),
    )
    parser.add_argument(
        "--official-materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment"
        ),
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def by_view(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("view_id")): row
        for row in rows
        if row.get("level") == "overall" or "level" not in row
    }


def metric_value(rows_by_view: dict[str, dict[str, Any]], view: str, key: str) -> float | None:
    return to_float(rows_by_view.get(view, {}).get(key))


def g_vector(row: dict[str, Any]) -> dict[str, float]:
    blocks = row.get("feature_blocks", {})
    g = blocks.get("G_e", {}) if isinstance(blocks, dict) else {}
    vector = g.get("g_e_feature_vector", {}) if isinstance(g, dict) else {}
    if not isinstance(vector, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in vector.items():
        number = to_float(value)
        if number is not None:
            out[key] = number
    return out


def summarize_feature(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "max": None, "mean": None}
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def feature_drift_rows(train_rows: list[dict[str, Any]], official_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    train_values: dict[str, list[float]] = defaultdict(list)
    official_values: dict[str, list[float]] = defaultdict(list)
    for row in train_rows:
        for key, value in g_vector(row).items():
            train_values[key].append(value)
    for row in official_rows:
        for key, value in g_vector(row).items():
            official_values[key].append(value)

    priority = {
        "support_contact_likelihood_proxy",
        "surface_gap_subject_bottom_to_object_top",
        "abs_surface_gap_subject_bottom_to_object_top",
        "normal_alignment_abs",
        "surface_alignment_abs",
        "xy_overlap_min_ratio",
        "xy_overlap_subject_ratio",
        "subject_vertical_extent_ratio",
        "subject_principal_axis_upness",
        "object_normal_upness",
    }
    rows: list[dict[str, Any]] = []
    for feature in sorted(set(train_values) | set(official_values)):
        tv = train_values.get(feature, [])
        ov = official_values.get(feature, [])
        ts = summarize_feature(tv)
        os = summarize_feature(ov)
        train_min = ts["min"]
        train_max = ts["max"]
        outside = 0
        if train_min is not None and train_max is not None:
            outside = sum(1 for value in ov if value < train_min or value > train_max)
        rows.append(
            {
                "feature": feature,
                "priority_feature": feature in priority,
                "train_count": len(tv),
                "official_count": len(ov),
                "train_min": train_min,
                "train_max": train_max,
                "train_mean": ts["mean"],
                "official_min": os["min"],
                "official_max": os["max"],
                "official_mean": os["mean"],
                "official_outside_train_range_count": outside,
                "official_outside_train_range_rate": outside / len(ov) if ov else None,
            }
        )
    return rows


def review_flags(dev_rows: list[dict[str, Any]], official_rows: list[dict[str, Any]], control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dev = by_view(dev_rows)
    official = by_view(official_rows)
    controls = {row.get("comparison"): row for row in control_rows}
    m4_dev = metric_value(dev, "M4_TxG_compatibility", "auroc")
    m4_official = metric_value(official, "M4_TxG_compatibility", "auroc")
    m2_official = metric_value(official, "M2_geometry_only", "auroc")
    m3_official = metric_value(official, "M3_T_plus_G_concat", "auroc")
    wrong_t = metric_value(official, "C1_wrong_T_same_route", "auroc")
    flags = [
        {
            "flag": "internal_dev_m4_above_baselines",
            "severity": "info",
            "value": m4_dev,
            "triggered": bool(m4_dev is not None and m4_dev > 0.7),
            "interpretation": "internal dev still shows compatibility signal before official validation transfer",
        },
        {
            "flag": "official_m4_below_random",
            "severity": "high",
            "value": m4_official,
            "triggered": bool(m4_official is not None and m4_official < 0.5),
            "interpretation": "official validation score direction or train/official target-feature alignment requires review",
        },
        {
            "flag": "official_m4_under_geometry_only",
            "severity": "high",
            "value": None if m4_official is None or m2_official is None else m4_official - m2_official,
            "triggered": bool(m4_official is not None and m2_official is not None and m4_official < m2_official),
            "interpretation": "hard-route compatibility is not yet stronger than geometry-only on official validation",
        },
        {
            "flag": "official_m4_under_concat",
            "severity": "high",
            "value": None if m4_official is None or m3_official is None else m4_official - m3_official,
            "triggered": bool(m4_official is not None and m3_official is not None and m4_official < m3_official),
            "interpretation": "interaction features do not transfer beyond simple T+G concat in this run",
        },
        {
            "flag": "wrong_t_inversion",
            "severity": "high",
            "value": wrong_t,
            "triggered": bool(wrong_t is not None and m4_official is not None and wrong_t > m4_official),
            "interpretation": "wrong-predicate control outperforming M4 is a blocker for paper-facing support/contact claim",
        },
    ]
    for comparison in ["M4_vs_M1", "M4_vs_M2", "M4_vs_M3", "M4_vs_wrong_T"]:
        row = controls.get(comparison, {})
        flags.append(
            {
                "flag": f"control_contract_{comparison}",
                "severity": "info",
                "value": row.get("delta_auroc"),
                "triggered": True,
                "interpretation": row.get("expectation", "missing"),
            }
        )
    return flags


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    runtime_dir = (repo_root / args.runtime_dir).resolve() if not args.runtime_dir.is_absolute() else args.runtime_dir
    alignment_dir = (repo_root / args.alignment_dir).resolve() if not args.alignment_dir.is_absolute() else args.alignment_dir
    protocol_dir = (repo_root / args.protocol_dir).resolve() if not args.protocol_dir.is_absolute() else args.protocol_dir
    official_dir = (repo_root / args.official_materialization_dir).resolve() if not args.official_materialization_dir.is_absolute() else args.official_materialization_dir
    out_dir = (repo_root / args.out).resolve() if not args.out.is_absolute() else args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    runtime_manifest = read_json(runtime_dir / "eval_manifest.json")
    alignment_summary = read_json(alignment_dir / "summary.json")
    protocol_summary = read_json(protocol_dir / "summary.json")
    runtime_errors = read_jsonl(runtime_dir / "validation_errors.jsonl")
    dev_metrics = read_csv(runtime_dir / "dev_metrics.csv")
    official_metrics = read_csv(runtime_dir / "official_metrics.csv")
    paired_metrics = read_csv(runtime_dir / "paired_group_metrics.csv")
    control_metrics = read_csv(runtime_dir / "control_metrics.csv")
    train_rows = read_jsonl(alignment_dir / "model_safe_no_class_train_dev.jsonl")
    official_rows = read_jsonl(official_dir / "model_safe_main_no_class.jsonl")

    if runtime_manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": runtime_manifest.get("status")})
    if runtime_manifest.get("next_todo") != EXPECTED_RUNTIME_NEXT:
        errors.append({"error_type": "unexpected_runtime_next_todo", "actual": runtime_manifest.get("next_todo")})
    if runtime_manifest.get("validation_errors") != 0 or runtime_errors:
        errors.append({"error_type": "runtime_validation_errors", "actual": runtime_manifest.get("validation_errors"), "rows": len(runtime_errors)})
    if alignment_summary.get("status") != EXPECTED_ALIGNMENT_STATUS:
        errors.append({"error_type": "unexpected_alignment_status", "actual": alignment_summary.get("status")})
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    decision = runtime_manifest.get("decision", {})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "official_test_usage_not_false", "actual": decision.get("official_test_usage")})
    if decision.get("paper_metric_promoted") is not False:
        errors.append({"error_type": "paper_metric_promoted_unexpected", "actual": decision.get("paper_metric_promoted")})

    flags = review_flags(dev_metrics, official_metrics, control_metrics)
    drift = feature_drift_rows(train_rows, official_rows)
    high_flags = [row for row in flags if row["severity"] == "high" and row["triggered"]]
    priority_drift = [
        row
        for row in drift
        if row["priority_feature"] and (to_float(row["official_outside_train_range_rate"]) or 0.0) > 0.2
    ]

    official = by_view(official_metrics)
    dev = by_view(dev_metrics)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "metric_warnings": len(high_flags),
        "selected_path": "support_contact_harder_metric_runner_ready_select_result_review" if not errors else "blocked_fix_metric_runner_outputs",
        "next_todo": EXPECTED_RUNTIME_NEXT if not errors else "fix_support_contact_harder_metric_runner_outputs",
        "input_artifacts": {
            "runtime_manifest": rel_path(repo_root, runtime_dir / "eval_manifest.json"),
            "alignment_summary": rel_path(repo_root, alignment_dir / "summary.json"),
            "protocol_summary": rel_path(repo_root, protocol_dir / "summary.json"),
            "official_materialization": rel_path(repo_root, official_dir),
        },
        "row_counts": runtime_manifest.get("row_counts", {}),
        "primary_metrics": {
            "internal_dev_m4_auroc": metric_value(dev, "M4_TxG_compatibility", "auroc"),
            "official_validation_m4_auroc": metric_value(official, "M4_TxG_compatibility", "auroc"),
            "official_validation_m2_geometry_auroc": metric_value(official, "M2_geometry_only", "auroc"),
            "official_validation_m3_concat_auroc": metric_value(official, "M3_T_plus_G_concat", "auroc"),
            "official_validation_wrong_t_auroc": metric_value(official, "C1_wrong_T_same_route", "auroc"),
        },
        "decision": {
            "runner_completed": not bool(errors),
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "support_contact_solved_claim_allowed": False,
            "metric_expectation_passed": False if high_flags else True,
            "result_review_next": not bool(errors),
            "feature_distribution_review_required": bool(priority_drift),
        },
        "output_artifacts": {
            "summary": rel_path(repo_root, out_dir / "summary.json"),
            "validation_errors": rel_path(repo_root, out_dir / "validation_errors.jsonl"),
            "review_flags": rel_path(repo_root, out_dir / "review_flags.csv"),
            "feature_drift": rel_path(repo_root, out_dir / "feature_drift.csv"),
            "official_metrics_snapshot": rel_path(repo_root, out_dir / "official_metrics_snapshot.csv"),
            "dev_metrics_snapshot": rel_path(repo_root, out_dir / "dev_metrics_snapshot.csv"),
            "control_metrics_snapshot": rel_path(repo_root, out_dir / "control_metrics_snapshot.csv"),
            "paired_group_metrics_snapshot": rel_path(repo_root, out_dir / "paired_group_metrics_snapshot.csv"),
            "next_contract": rel_path(repo_root, out_dir / "next_contract.json"),
            "report": rel_path(repo_root, out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_result_review" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "must_review": [
            "official M4 below random and below geometry-only",
            "wrong-T control outperforming correct T",
            "train-aligned vs official G_e feature distribution shift",
            "support/contact solved-family wording remains blocked",
        ],
        "blocked_until_review": ["paper_metric_promotion", "support_contact_solved_claim", "source_reranking", "p_obs_p_rel"],
    }

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "review_flags.csv", flags)
    write_csv(out_dir / "feature_drift.csv", drift)
    write_csv(out_dir / "official_metrics_snapshot.csv", official_metrics)
    write_csv(out_dir / "dev_metrics_snapshot.csv", dev_metrics)
    write_csv(out_dir / "control_metrics_snapshot.csv", control_metrics)
    write_csv(out_dir / "paired_group_metrics_snapshot.csv", paired_metrics)

    report = [
        "# Support/Contact Harder Route Metric Runner Review",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"metric_warnings = {summary['metric_warnings']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "This stage verifies that the Docker metric runner completed and records non-promoted metric warnings.",
        "It does not promote support/contact as a solved paper result.",
        "",
        "## Primary Metrics",
        "",
        "```json",
        json.dumps(summary["primary_metrics"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## High Warnings",
        "",
    ]
    if high_flags:
        for row in high_flags:
            report.append(f"- {row['flag']}: {row['interpretation']}")
    else:
        report.append("- none")
    report.extend(
        [
            "",
            "## Interpretation",
            "",
            "Internal dev shows an M4 compatibility signal, but official validation currently fails the expected support/contact hard-route pattern.",
            "The next stage must review whether this is caused by target construction mismatch, feature distribution shift, sign convention, or source-domain mismatch.",
        ]
    )
    (out_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return summary


def main() -> int:
    summary = run(parse_args())
    return 1 if summary["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
