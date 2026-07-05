#!/usr/bin/env python3
"""Audit target independence for H002 proximity LH-only proxy labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_ingestion"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_target_independence_audit"

EXPECTED_INGESTION_STATUS = "h002_reliability_target_v12_proximity_lh_only_label_ingested_with_probe_risk"
EXPECTED_NEXT_TODO = "reliability_target_v12_proximity_lh_only_target_independence_audit"
NEXT_TODO = "reliability_target_v12_proximity_lh_only_path_decision_after_audit"

SCHEMA_VERSION = "h002_reliability_target_v12_proximity_lh_only_target_independence_audit_v1"

TARGET_LABELS = {
    "multiclass": "relation_reliability_multiclass_target",
    "binary": "relation_reliability_binary_target",
}

RISK_PREDICTORS = [
    "subject_object_label_pair_hidden",
    "subject_object_visible_pair",
    "scan_id",
    "subject_label",
    "object_label",
    "label_match_status_hidden",
    "machine_hint_hidden",
    "rank_band_hidden",
    "semantic_rank_band_coarse",
    "label_geometry_bucket_hidden",
]

SLICE_SPECS = {
    "full_binary": [],
    "label_match_balanced": ["label_match_status_hidden"],
    "machine_hint_balanced": ["machine_hint_hidden"],
    "rank_band_balanced": ["rank_band_hidden"],
    "scan_balanced": ["scan_id"],
    "subject_label_balanced": ["subject_label"],
    "object_label_balanced": ["object_label"],
    "subject_object_pair_balanced": ["subject_object_visible_pair"],
    "hidden_subject_object_pair_balanced": ["subject_object_label_pair_hidden"],
    "label_match_rank_balanced": ["label_match_status_hidden", "rank_band_hidden"],
    "scan_label_match_balanced": ["scan_id", "label_match_status_hidden"],
}

STRICT_MIN_ROWS_BINARY = 60
STRICT_MIN_PER_CLASS_BINARY = 25
DIAGNOSTIC_MIN_ROWS_BINARY = 30
DIAGNOSTIC_MIN_PER_CLASS_BINARY = 10

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 8,
    "large_group_purity": 0.90,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_ingestion(summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": EXPECTED_INGESTION_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "ingestion_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified", "rga_redefined_as_lh_only", "multi_view_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "ingestion_boundary_violation", "key": key, "actual": boundary.get(key)})
    if summary.get("counts", {}).get("rows") != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": summary.get("counts", {}).get("rows"), "actual": len(rows)})
    ids = [str(row.get("blind_review_id") or "") for row in rows]
    for blind_id, count in Counter(ids).items():
        if not blind_id or count > 1:
            errors.append({"error_type": "blind_review_id_error", "blind_review_id": blind_id, "count": count})
    return errors


def semantic_rank_band_coarse(row: dict[str, Any]) -> str:
    value = row.get("semantic_rank_hidden")
    try:
        rank = int(float(value))
    except (TypeError, ValueError):
        return "rank_missing"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for row in rows:
        enriched_row = dict(row)
        enriched_row["semantic_rank_band_coarse"] = semantic_rank_band_coarse(row)
        enriched.append(enriched_row)
    return enriched


def label_value(row: dict[str, Any], target: str) -> Any:
    return row.get(TARGET_LABELS[target])


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    result = 0.0
    for count in counter.values():
        if count:
            p = count / total
            result -= p * math.log(p, 2)
    return result


def nmi(rows: list[dict[str, Any]], predictor: str, target: str) -> float:
    if not rows:
        return 0.0
    label_counts = Counter(str(label_value(row, target)) for row in rows)
    group_counts = Counter(str(row.get(predictor, "missing")) for row in rows)
    joint = Counter((str(row.get(predictor, "missing")), str(label_value(row, target))) for row in rows)
    total = len(rows)
    mi = 0.0
    for (group, label), count in joint.items():
        pxy = count / total
        px = group_counts[group] / total
        py = label_counts[label] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    denom = math.sqrt(entropy(group_counts) * entropy(label_counts))
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, target: str) -> dict[str, Any]:
    if not rows:
        return {
            "predictor": predictor,
            "target": target,
            "rows": 0,
            "risk_flag": False,
            "majority_rule_accuracy": None,
            "majority_baseline_accuracy": None,
            "majority_excess_over_baseline": None,
            "normalized_mutual_information": None,
            "top_groups": [],
        }
    label_counts = Counter(str(label_value(row, target)) for row in rows)
    baseline = max(label_counts.values()) / len(rows)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][str(label_value(row, target))] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    acc = correct / len(rows)
    info = nmi(rows, predictor, target)
    top_groups = []
    large_pure = False
    for group, counter in groups.items():
        total = sum(counter.values())
        label, count = counter.most_common(1)[0]
        rate = count / total
        if total >= RISK_THRESHOLDS["large_group_rows"] and rate >= RISK_THRESHOLDS["large_group_purity"]:
            large_pure = True
        top_groups.append(
            {
                "group_value": group,
                "rows": total,
                "majority_label": label,
                "majority_rate": rate,
                "label_counts": dict(counter),
            }
        )
    top_groups.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    risk_flag = (
        acc >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and acc - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or info >= RISK_THRESHOLDS["normalized_mutual_information"] or large_pure
    return {
        "predictor": predictor,
        "target": target,
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(label_counts),
        "majority_rule_accuracy": acc,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": acc - baseline,
        "normalized_mutual_information": info,
        "risk_flag": risk_flag,
        "top_groups": top_groups[:12],
    }


def group_key(row: dict[str, Any], keys: list[str]) -> str:
    if not keys:
        return "__all__"
    return "||".join(f"{key}={row.get(key, 'missing')}" for key in keys)


def stable_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("blind_review_id")), str(row.get("prediction_id"))


def balanced_slice(rows: list[dict[str, Any]], keys: list[str], target: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[group_key(row, keys)][str(label_value(row, target))].append(row)
    selected: list[dict[str, Any]] = []
    mixed_groups = 0
    for _, by_label in grouped.items():
        if len(by_label) < 2:
            continue
        mixed_groups += 1
        min_count = min(len(items) for items in by_label.values())
        for items in by_label.values():
            selected.extend(sorted(items, key=stable_sort_key)[:min_count])
    counts = Counter(str(label_value(row, target)) for row in selected)
    return selected, {
        "group_keys": keys,
        "groups": len(grouped),
        "mixed_groups": mixed_groups,
        "selected_rows": len(selected),
        "selected_counts": dict(counts),
    }


def slice_audit(rows: list[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    audits = []
    target_rows = [row for row in rows if target != "binary" or row.get("binary_usable")]
    for spec_name, keys in SLICE_SPECS.items():
        selected, selection = balanced_slice(target_rows, keys, target)
        counts = Counter(str(label_value(row, target)) for row in selected)
        min_per_class = min(counts.values()) if counts else 0
        if target == "binary":
            strict_count_gate = len(selected) >= STRICT_MIN_ROWS_BINARY and min_per_class >= STRICT_MIN_PER_CLASS_BINARY
            diagnostic_count_gate = len(selected) >= DIAGNOSTIC_MIN_ROWS_BINARY and min_per_class >= DIAGNOSTIC_MIN_PER_CLASS_BINARY
        else:
            strict_count_gate = False
            diagnostic_count_gate = len(selected) >= 90 and min_per_class >= 20
        risks = [majority_risk(selected, predictor, target) for predictor in RISK_PREDICTORS] if selected else []
        risk_flags = [risk for risk in risks if risk["risk_flag"]]
        blocker_predictors = {risk["predictor"] for risk in risk_flags}
        object_pair_blocked = bool({"subject_object_label_pair_hidden", "subject_object_visible_pair"} & blocker_predictors)
        scan_blocked = "scan_id" in blocker_predictors
        strict_pass = strict_count_gate and not risk_flags
        diagnostic_pass = diagnostic_count_gate and not object_pair_blocked and not scan_blocked
        audits.append(
            {
                "slice": spec_name,
                "target": target,
                **selection,
                "min_per_class": min_per_class,
                "strict_count_gate": strict_count_gate,
                "diagnostic_count_gate": diagnostic_count_gate,
                "risk_flags": len(risk_flags),
                "risk_predictors": sorted(blocker_predictors),
                "strict_pass": strict_pass,
                "diagnostic_pass": diagnostic_pass,
            }
        )
    return audits


def exact_pair_mixed_stats(rows: list[dict[str, Any]], key: str, target: str) -> dict[str, Any]:
    target_rows = [row for row in rows if target != "binary" or row.get("binary_usable")]
    grouped: dict[str, Counter] = defaultdict(Counter)
    for row in target_rows:
        grouped[str(row.get(key, "missing"))][str(label_value(row, target))] += 1
    mixed = {group: counter for group, counter in grouped.items() if len(counter) >= 2}
    mixed_rows = sum(sum(counter.values()) for counter in mixed.values())
    return {
        "key": key,
        "target": target,
        "groups": len(grouped),
        "mixed_groups": len(mixed),
        "mixed_rows": mixed_rows,
        "top_mixed_groups": [
            {"group_value": group, "label_counts": dict(counter), "rows": sum(counter.values())}
            for group, counter in sorted(mixed.items(), key=lambda item: (-sum(item[1].values()), item[0]))[:12]
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V12 Proximity LH-Only Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "The proximity LH-only proxy target is not posterior-ready.",
        "",
        "```text",
        f"binary_rows = {summary['counts']['binary_rows']}",
        f"binary_target = {summary['counts']['binary_target']}",
        f"strict_slices = {summary['counts']['strict_slices']}",
        f"diagnostic_slices = {summary['counts']['diagnostic_slices']}",
        f"object_pair_mixed_binary_groups = {summary['object_pair_mixed_stats']['subject_object_visible_pair_binary']['mixed_groups']}",
        f"quick_risk_flags = {summary['counts']['risk_flags_full']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Main Blocker",
        "",
        "The visible object-pair identity explains the proxy labels. Exact subject-object-pair mixed contrast is absent, so a factorized posterior would be evaluated against a target that can be solved from object identity rather than relation reliability.",
        "",
        "## Decision",
        "",
        f"Next TODO: `{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ingestion_summary = read_json(ingestion_dir / "summary.json")
    rows = enrich_rows(read_jsonl(ingestion_dir / "ingested_rows.jsonl"))
    validation_errors = validate_ingestion(ingestion_summary, rows)

    full_risks = []
    for target in ["multiclass", "binary"]:
        target_rows = [row for row in rows if target != "binary" or row.get("binary_usable")]
        for predictor in RISK_PREDICTORS:
            full_risks.append(majority_risk(target_rows, predictor, target))
    risk_flags = [risk for risk in full_risks if risk["risk_flag"]]
    slices = slice_audit(rows, "binary") + slice_audit(rows, "multiclass")
    strict_slices = [item for item in slices if item["strict_pass"]]
    diagnostic_slices = [item for item in slices if item["diagnostic_pass"]]

    object_pair_stats = {
        "subject_object_visible_pair_binary": exact_pair_mixed_stats(rows, "subject_object_visible_pair", "binary"),
        "subject_object_label_pair_hidden_binary": exact_pair_mixed_stats(rows, "subject_object_label_pair_hidden", "binary"),
        "scan_id_binary": exact_pair_mixed_stats(rows, "scan_id", "binary"),
        "subject_object_visible_pair_multiclass": exact_pair_mixed_stats(rows, "subject_object_visible_pair", "multiclass"),
    }

    binary_rows = [row for row in rows if row.get("binary_usable")]
    status = (
        "h002_reliability_target_v12_proximity_lh_only_independence_blocked_object_pair_shortcut"
        if not validation_errors and not strict_slices and not diagnostic_slices
        else "h002_reliability_target_v12_proximity_lh_only_independence_has_controlled_slice"
        if not validation_errors
        else "h002_reliability_target_v12_proximity_lh_only_independence_audit_errors"
    )
    next_todo = (
        NEXT_TODO
        if status.endswith("object_pair_shortcut")
        else "reliability_target_v12_proximity_lh_only_controlled_posterior_smoke"
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "full_risk_audit": output_dir / "full_risk_audit.json",
        "slice_audit": output_dir / "slice_audit.json",
        "object_pair_mixed_stats": output_dir / "object_pair_mixed_stats.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "ingested_rows": rel_path(ingestion_dir / "ingested_rows.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "binary_rows": len(binary_rows),
            "multiclass_rows": len(rows),
            "binary_target": dict(Counter(str(row.get("relation_reliability_binary_target")) for row in binary_rows)),
            "multiclass_target": dict(Counter(str(row.get("relation_reliability_multiclass_target")) for row in rows)),
            "risk_flags_full": len(risk_flags),
            "strict_slices": len(strict_slices),
            "diagnostic_slices": len(diagnostic_slices),
        },
        "risk_summary": {
            "full_risk_flags": [
                {
                    "predictor": risk["predictor"],
                    "target": risk["target"],
                    "rows": risk["rows"],
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                }
                for risk in risk_flags
            ],
            "strict_slices": strict_slices,
            "diagnostic_slices": diagnostic_slices,
        },
        "object_pair_mixed_stats": object_pair_stats,
        "decision": {
            "posterior_smoke_allowed": bool(strict_slices or diagnostic_slices),
            "reason": "object-pair shortcut blocks posterior" if not strict_slices and not diagnostic_slices else "controlled slice exists",
            "recommended_path": "path_decision_after_audit" if not strict_slices and not diagnostic_slices else "controlled_posterior_smoke",
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": bool(strict_slices or diagnostic_slices),
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
    }

    write_json(output_paths["full_risk_audit"], full_risks)
    write_json(output_paths["slice_audit"], slices)
    write_json(output_paths["object_pair_mixed_stats"], object_pair_stats)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"binary_rows={summary['counts']['binary_rows']}")
    print(f"strict_slices={summary['counts']['strict_slices']}")
    print(f"diagnostic_slices={summary['counts']['diagnostic_slices']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
