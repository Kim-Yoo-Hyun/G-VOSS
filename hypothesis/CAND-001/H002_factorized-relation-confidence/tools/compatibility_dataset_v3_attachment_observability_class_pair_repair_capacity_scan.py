#!/usr/bin/env python3
"""Scan exact class-pair repair capacity for R7 attachment observability."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v17_attachment_deferred_witness_schema_capacity_scan as v17
import reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan as v21


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"
RGA_ROOT = ARTIFACT_ROOT / "train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_ready"
)
EXPECTED_PLAN_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_blocked_insufficient_exact_class_pair_capacity"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_input_errors"
)

NEXT_TODO_READY = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining"
)
NEXT_TODO_BLOCKED = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_capacity_scan"
)

PRIMARY_PREDICATES = ("attached to", "hanging on")
DIAGNOSTIC_PREDICATES = ("connected to",)
ROLE_ACCEPT = v21.ROLE_ACCEPT_PROXY
ROLE_REJECT = v21.ROLE_REJECT_PROXY
ROLE_UNCERTAIN = v21.ROLE_UNCERTAIN_PROXY

AXIS_SPECS: list[tuple[str, list[str]]] = [
    ("exact_predicate_class_pair", ["predicate_label", "subject_label", "object_label"]),
    (
        "exact_predicate_class_pair_rank",
        ["predicate_label", "subject_label", "object_label", "rank_band"],
    ),
    (
        "exact_predicate_class_pair_coverage",
        ["predicate_label", "subject_label", "object_label", "coverage_proxy"],
    ),
    (
        "exact_predicate_class_pair_geometry",
        ["predicate_label", "subject_label", "object_label", "geometry_bucket"],
    ),
    (
        "exact_predicate_class_pair_rank_coverage",
        ["predicate_label", "subject_label", "object_label", "rank_band", "coverage_proxy"],
    ),
    (
        "family_pair_fallback",
        ["predicate_label", "object_family_pair"],
    ),
]

SCAN_SHARE_CAP = 0.08
MIN_BALANCED_PRIMARY_ROWS = 400
MIN_POSITIVE_ROWS = 100
MIN_EXACT_MIXED_STRATA = 20
MIN_PER_PREDICATE_MIXED_STRATA = 10
MIN_PER_PREDICATE_BALANCED_ROWS = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(plan_summary: dict[str, Any], contract: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    if contract.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_contract_next", "actual": contract.get("next_todo")})
    if contract.get("target_control_axis") != "predicate_label + subject_label + object_label":
        errors.append({"error_type": "unexpected_target_control_axis", "actual": contract.get("target_control_axis")})
    gates = contract.get("minimum_capacity_gates", {})
    expected = {
        "balanced_primary_rows": MIN_BALANCED_PRIMARY_ROWS,
        "positive_rows": MIN_POSITIVE_ROWS,
        "exact_predicate_class_pair_mixed_strata": MIN_EXACT_MIXED_STRATA,
    }
    for key, value in expected.items():
        if int(gates.get(key, -1)) != value:
            errors.append({"error_type": "unexpected_capacity_gate", "key": key, "actual": gates.get(key)})
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "materializes_rows",
        "packet_materialization_started",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def make_empty_group(spec_name: str, fields: list[str], values: tuple[str, ...]) -> dict[str, Any]:
    return {
        "spec_name": spec_name,
        "fields": fields,
        "values": values,
        "rows": 0,
        "role_counts": Counter(),
        "scan_counts": defaultdict(Counter),
        "rank_counts": Counter(),
        "geometry_counts": Counter(),
        "coverage_counts": Counter(),
        "uncertainty_counts": Counter(),
        "samples": defaultdict(list),
    }


def group_key(candidate: dict[str, Any], fields: list[str]) -> tuple[str, ...]:
    return tuple(str(candidate.get(field)) for field in fields)


def add_sample(group: dict[str, Any], candidate: dict[str, Any]) -> None:
    role = candidate["reliability_proxy_role"]
    if len(group["samples"][role]) >= 3:
        return
    group["samples"][role].append(
        {
            "prediction_id": candidate["prediction_id"],
            "scan_id": candidate["scan_id"],
            "subject_label": candidate["subject_label"],
            "predicate_label": candidate["predicate_label"],
            "object_label": candidate["object_label"],
            "rank_band": candidate["rank_band"],
            "geometry_bucket": candidate["geometry_bucket"],
            "coverage_proxy": candidate["coverage_proxy"],
            "uncertainty_bucket": candidate["uncertainty_bucket"],
            "anchor_bucket": candidate["anchor_bucket_hidden"],
            "gt_label_match_status": candidate["gt_label_match_status"],
        }
    )


def update_group(group: dict[str, Any], candidate: dict[str, Any]) -> None:
    role = candidate["reliability_proxy_role"]
    group["rows"] += 1
    group["role_counts"][role] += 1
    group["scan_counts"][role][str(candidate["scan_id"])] += 1
    group["rank_counts"][candidate["rank_band"]] += 1
    group["geometry_counts"][candidate["geometry_bucket"]] += 1
    group["coverage_counts"][candidate["coverage_proxy"]] += 1
    group["uncertainty_counts"][candidate["uncertainty_bucket"]] += 1
    add_sample(group, candidate)


def scan_capped_count(counter: Counter[str], target_rows: int) -> int:
    if target_rows <= 0:
        return 0
    cap = max(1, int(target_rows * SCAN_SHARE_CAP))
    return sum(min(count, cap) for count in counter.values())


def scan_capped_balanced_rows(group: dict[str, Any], raw_pairs: int) -> int:
    for pairs in range(raw_pairs, 0, -1):
        if (
            scan_capped_count(group["scan_counts"][ROLE_ACCEPT], pairs) >= pairs
            and scan_capped_count(group["scan_counts"][ROLE_REJECT], pairs) >= pairs
        ):
            return pairs * 2
    return 0


def finalize_group(group: dict[str, Any]) -> dict[str, Any]:
    accept = int(group["role_counts"].get(ROLE_ACCEPT, 0))
    reject = int(group["role_counts"].get(ROLE_REJECT, 0))
    uncertain = int(group["role_counts"].get(ROLE_UNCERTAIN, 0))
    raw_pairs = min(accept, reject)
    raw_rows = raw_pairs * 2
    scan_rows = scan_capped_balanced_rows(group, raw_pairs)
    values = tuple(group["values"])
    predicate = values[0] if values else ""
    return {
        "spec_name": group["spec_name"],
        "fields": ",".join(group["fields"]),
        "group_value": " | ".join(values),
        "predicate_label": predicate,
        "rows": int(group["rows"]),
        "accept_proxy_rows": accept,
        "reject_proxy_rows": reject,
        "uncertain_proxy_rows": uncertain,
        "raw_balanced_rows": raw_rows,
        "scan_capped_balanced_rows": scan_rows,
        "is_accept_reject_mixed": raw_pairs > 0,
        "accept_scan_count": len(group["scan_counts"][ROLE_ACCEPT]),
        "reject_scan_count": len(group["scan_counts"][ROLE_REJECT]),
        "rank_counts": dict(group["rank_counts"]),
        "geometry_counts": dict(group["geometry_counts"]),
        "coverage_counts": dict(group["coverage_counts"]),
        "uncertainty_counts": dict(group["uncertainty_counts"]),
        "samples": {key: value for key, value in group["samples"].items()},
    }


def scan_full_train(match_rows: Path) -> dict[str, Any]:
    pair_geometry, raw_join = v17.collect_pair_geometry(match_rows)
    groups: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    distinct: dict[str, set[str]] = defaultdict(set)
    primary_rows = 0
    diagnostic_rows = 0
    joined_rows = 0

    for _, row in v17.iter_jsonl(match_rows):
        predicate_info = row.get("predicate", {})
        if predicate_info.get("predicate_family") != "attachment_deferred":
            continue
        predicate = v17.norm(predicate_info.get("predicate_label"))
        if predicate not in PRIMARY_PREDICATES and predicate not in DIAGNOSTIC_PREDICATES:
            continue

        identity = row.get("identity", {})
        pair_id = identity.get("directed_pair_id")
        raw_entry = pair_geometry.get(pair_id)
        witness = v17.classify_attachment(row, raw_entry)
        if raw_entry is not None:
            joined_rows += 1

        if predicate in DIAGNOSTIC_PREDICATES:
            diagnostic_rows += 1
            counts["diagnostic_predicate"][predicate] += 1
            counts["diagnostic_cell"][witness["cell_id"]] += 1
            continue

        primary_rows += 1
        candidate = v21.candidate_from_row(row, witness, raw_entry)
        role = candidate["reliability_proxy_role"]
        counts["predicate"][predicate] += 1
        counts["role"][role] += 1
        counts["predicate_role"][f"{predicate}|{role}"] += 1
        counts["rank_band"][candidate["rank_band"]] += 1
        counts["geometry_bucket"][candidate["geometry_bucket"]] += 1
        counts["coverage_proxy"][candidate["coverage_proxy"]] += 1
        counts["uncertainty_bucket"][candidate["uncertainty_bucket"]] += 1
        counts["object_family_pair"][candidate["object_family_pair"]] += 1
        counts["visible_endpoint_pair"][candidate["visible_endpoint_pair"]] += 1
        distinct["scan_id"].add(str(candidate["scan_id"]))
        distinct["subgraph_id"].add(str(candidate["subgraph_id"]))
        distinct["directed_pair_id"].add(str(candidate["directed_pair_id"]))
        distinct["visible_endpoint_pair"].add(candidate["visible_endpoint_pair"])

        for spec_name, fields in AXIS_SPECS:
            values = group_key(candidate, fields)
            key = (spec_name, values)
            if key not in groups:
                groups[key] = make_empty_group(spec_name, fields, values)
            update_group(groups[key], candidate)

    finalized = [finalize_group(group) for group in groups.values()]
    return {
        "raw_join": raw_join,
        "counts": counts,
        "diagnostic_rows": diagnostic_rows,
        "distinct": {key: len(value) for key, value in distinct.items()},
        "groups": finalized,
        "joined_rows": joined_rows,
        "primary_rows": primary_rows,
    }


def summarize_axes(groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_axis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        by_axis[group["spec_name"]].append(group)

    axis_rows: list[dict[str, Any]] = []
    predicate_axis_rows: list[dict[str, Any]] = []
    for spec_name, rows in sorted(by_axis.items()):
        mixed = [row for row in rows if row["is_accept_reject_mixed"]]
        axis_rows.append(
            {
                "spec_name": spec_name,
                "groups": len(rows),
                "mixed_groups": len(mixed),
                "rows": sum(int(row["rows"]) for row in rows),
                "accept_proxy_rows": sum(int(row["accept_proxy_rows"]) for row in rows),
                "reject_proxy_rows": sum(int(row["reject_proxy_rows"]) for row in rows),
                "uncertain_proxy_rows": sum(int(row["uncertain_proxy_rows"]) for row in rows),
                "raw_balanced_rows": sum(int(row["raw_balanced_rows"]) for row in mixed),
                "scan_capped_balanced_rows": sum(int(row["scan_capped_balanced_rows"]) for row in mixed),
            }
        )
        for predicate in PRIMARY_PREDICATES:
            pred_rows = [row for row in rows if row["predicate_label"] == predicate]
            pred_mixed = [row for row in pred_rows if row["is_accept_reject_mixed"]]
            predicate_axis_rows.append(
                {
                    "spec_name": spec_name,
                    "predicate_label": predicate,
                    "groups": len(pred_rows),
                    "mixed_groups": len(pred_mixed),
                    "rows": sum(int(row["rows"]) for row in pred_rows),
                    "accept_proxy_rows": sum(int(row["accept_proxy_rows"]) for row in pred_rows),
                    "reject_proxy_rows": sum(int(row["reject_proxy_rows"]) for row in pred_rows),
                    "uncertain_proxy_rows": sum(int(row["uncertain_proxy_rows"]) for row in pred_rows),
                    "raw_balanced_rows": sum(int(row["raw_balanced_rows"]) for row in pred_mixed),
                    "scan_capped_balanced_rows": sum(int(row["scan_capped_balanced_rows"]) for row in pred_mixed),
                }
            )
    return axis_rows, predicate_axis_rows


def top_strata(groups: list[dict[str, Any]], limit_per_axis: int = 80) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    by_axis: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        by_axis[group["spec_name"]].append(group)
    for spec_name, rows in sorted(by_axis.items()):
        rows = sorted(
            rows,
            key=lambda row: (
                -int(row["scan_capped_balanced_rows"]),
                -int(row["raw_balanced_rows"]),
                -int(row["rows"]),
                row["group_value"],
            ),
        )
        for row in rows[:limit_per_axis]:
            out.append(
                {
                    "spec_name": spec_name,
                    "group_value": row["group_value"],
                    "predicate_label": row["predicate_label"],
                    "rows": row["rows"],
                    "accept_proxy_rows": row["accept_proxy_rows"],
                    "reject_proxy_rows": row["reject_proxy_rows"],
                    "uncertain_proxy_rows": row["uncertain_proxy_rows"],
                    "raw_balanced_rows": row["raw_balanced_rows"],
                    "scan_capped_balanced_rows": row["scan_capped_balanced_rows"],
                    "accept_scan_count": row["accept_scan_count"],
                    "reject_scan_count": row["reject_scan_count"],
                    "rank_counts": json.dumps(row["rank_counts"], ensure_ascii=False, sort_keys=True),
                    "geometry_counts": json.dumps(row["geometry_counts"], ensure_ascii=False, sort_keys=True),
                    "coverage_counts": json.dumps(row["coverage_counts"], ensure_ascii=False, sort_keys=True),
                    "uncertainty_counts": json.dumps(row["uncertainty_counts"], ensure_ascii=False, sort_keys=True),
                }
            )
    return out


def axis_lookup(rows: list[dict[str, Any]], spec_name: str) -> dict[str, Any]:
    for row in rows:
        if row["spec_name"] == spec_name:
            return row
    return {}


def predicate_lookup(rows: list[dict[str, Any]], spec_name: str, predicate: str) -> dict[str, Any]:
    for row in rows:
        if row["spec_name"] == spec_name and row["predicate_label"] == predicate:
            return row
    return {}


def decision(axis_rows: list[dict[str, Any]], predicate_axis_rows: list[dict[str, Any]]) -> dict[str, Any]:
    strict = axis_lookup(axis_rows, "exact_predicate_class_pair")
    checks = {
        "balanced_primary_rows_min": int(strict.get("scan_capped_balanced_rows", 0)) >= MIN_BALANCED_PRIMARY_ROWS,
        "positive_rows_min": int(strict.get("scan_capped_balanced_rows", 0)) // 2 >= MIN_POSITIVE_ROWS,
        "exact_predicate_class_pair_mixed_strata_min": int(strict.get("mixed_groups", 0)) >= MIN_EXACT_MIXED_STRATA,
    }
    for predicate in PRIMARY_PREDICATES:
        pred = predicate_lookup(predicate_axis_rows, "exact_predicate_class_pair", predicate)
        checks[f"{predicate}_mixed_strata_min"] = int(pred.get("mixed_groups", 0)) >= MIN_PER_PREDICATE_MIXED_STRATA
        checks[f"{predicate}_balanced_rows_min"] = int(pred.get("scan_capped_balanced_rows", 0)) >= MIN_PER_PREDICATE_BALANCED_ROWS
    capacity_pass = all(checks.values())
    failed = [name for name, ok in checks.items() if not ok]
    return {
        "capacity_pass": capacity_pass,
        "checks": checks,
        "failed_checks": failed,
        "minimum_gates": {
            "balanced_primary_rows": MIN_BALANCED_PRIMARY_ROWS,
            "exact_predicate_class_pair_mixed_strata": MIN_EXACT_MIXED_STRATA,
            "per_predicate_balanced_rows": MIN_PER_PREDICATE_BALANCED_ROWS,
            "per_predicate_mixed_strata": MIN_PER_PREDICATE_MIXED_STRATA,
            "positive_rows": MIN_POSITIVE_ROWS,
            "scan_share_cap": SCAN_SHARE_CAP,
        },
        "next_todo": NEXT_TODO_READY if capacity_pass else NEXT_TODO_BLOCKED,
        "selected_route": (
            "exact_predicate_class_pair_repair_candidate_mining"
            if capacity_pass
            else "path_decision_required_after_exact_class_pair_capacity_scan"
        ),
    }


def build_report(summary: dict[str, Any], axis_rows: list[dict[str, Any]], predicate_axis_rows: list[dict[str, Any]]) -> str:
    decision_payload = summary["capacity_decision"]
    strict = axis_lookup(axis_rows, "exact_predicate_class_pair")
    lines = [
        "# H002 R7 Attachment Observability Class-Pair Repair Capacity Scan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Exact Predicate/Class-Pair Capacity",
        "",
        "```text",
        f"mixed_groups = {strict.get('mixed_groups', 0)}",
        f"scan_capped_balanced_rows = {strict.get('scan_capped_balanced_rows', 0)}",
        f"raw_balanced_rows = {strict.get('raw_balanced_rows', 0)}",
        f"accept_proxy_rows = {strict.get('accept_proxy_rows', 0)}",
        f"reject_proxy_rows = {strict.get('reject_proxy_rows', 0)}",
        "```",
        "",
        "Per predicate:",
        "",
        "| Predicate | Mixed Groups | Scan-Capped Balanced Rows | Accept Proxy | Reject Proxy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for predicate in PRIMARY_PREDICATES:
        row = predicate_lookup(predicate_axis_rows, "exact_predicate_class_pair", predicate)
        lines.append(
            f"| `{predicate}` | {row.get('mixed_groups', 0)} | {row.get('scan_capped_balanced_rows', 0)} | {row.get('accept_proxy_rows', 0)} | {row.get('reject_proxy_rows', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- capacity_pass = `{decision_payload['capacity_pass']}`",
            f"- selected_route = `{decision_payload['selected_route']}`",
            f"- failed_checks = `{', '.join(decision_payload['failed_checks']) if decision_payload['failed_checks'] else 'none'}`",
            "",
            "Interpretation:",
            "",
            "- This is a train-only proxy-capacity scan, not a learned result.",
            "- `proxy_role`, `geometry_bucket`, `coverage_proxy`, rank, source confidence, and GT status remain hidden selection fields.",
            "- If promoted, candidate mining must still create packet rows, ingest labels, and pass a schema/shortcut audit before any learned smoke.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary_path = args.plan_dir / "summary.json"
    contract_path = args.plan_dir / "capacity_scan_contract.json"
    validation_errors: list[dict[str, Any]] = []
    if not plan_summary_path.exists():
        validation_errors.append({"error_type": "missing_plan_summary", "path": rel_path(plan_summary_path)})
        plan_summary: dict[str, Any] = {}
    else:
        plan_summary = read_json(plan_summary_path)
    if not contract_path.exists():
        validation_errors.append({"error_type": "missing_capacity_scan_contract", "path": rel_path(contract_path)})
        contract: dict[str, Any] = {}
    else:
        contract = read_json(contract_path)
    validation_errors.extend(validate_inputs(plan_summary, contract, args.match_rows))

    scan = scan_full_train(args.match_rows) if args.match_rows.exists() else {
        "counts": {},
        "diagnostic_rows": 0,
        "distinct": {},
        "groups": [],
        "joined_rows": 0,
        "primary_rows": 0,
        "raw_join": {},
    }
    axis_rows, predicate_axis_rows = summarize_axes(scan["groups"])
    top_rows = top_strata(scan["groups"])
    decision_payload = decision(axis_rows, predicate_axis_rows)

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "fix_inputs"
        next_todo = "fix_attachment_observability_class_pair_repair_capacity_scan_inputs"
    elif decision_payload["capacity_pass"]:
        status = STATUS_READY
        selected_path = decision_payload["selected_route"]
        next_todo = NEXT_TODO_READY
    else:
        status = STATUS_BLOCKED
        selected_path = decision_payload["selected_route"]
        next_todo = NEXT_TODO_BLOCKED
        validation_errors.append(
            {
                "error_type": "capacity_gate_not_passed",
                "failed_checks": decision_payload["failed_checks"],
                "scope": "R7_exact_predicate_subject_object_class_pair",
            }
        )

    output_paths = {
        "axis_capacity": args.output_dir / "axis_capacity.csv",
        "predicate_axis_capacity": args.output_dir / "predicate_axis_capacity.csv",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "top_strata": args.output_dir / "top_strata.csv",
        "top_strata_samples": args.output_dir / "top_strata_samples.jsonl",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    counts = scan["counts"]
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "packet_materialization_started": False,
            "paper_evidence_allowed": False,
            "proxy_capacity_only": True,
            "runs_learned_smoke": False,
            "split": "train_only_capacity_scan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "capacity_decision": decision_payload,
        "counts": {
            "coverage_proxy_counts": dict(counts.get("coverage_proxy", {})),
            "diagnostic_rows": scan["diagnostic_rows"],
            "distinct": scan["distinct"],
            "geometry_bucket_counts": dict(counts.get("geometry_bucket", {})),
            "joined_rows": scan["joined_rows"],
            "object_family_pair_counts_top20": dict(counts.get("object_family_pair", Counter()).most_common(20)),
            "predicate_counts": dict(counts.get("predicate", {})),
            "predicate_role_counts": dict(counts.get("predicate_role", {})),
            "primary_rows": scan["primary_rows"],
            "rank_band_counts": dict(counts.get("rank_band", {})),
            "role_counts": dict(counts.get("role", {})),
            "uncertainty_bucket_counts": dict(counts.get("uncertainty_bucket", {})),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "capacity_scan_contract": rel_path(contract_path),
            "match_rows": rel_path(args.match_rows),
            "mining_plan_summary": rel_path(plan_summary_path),
        },
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    sample_rows: list[dict[str, Any]] = []
    top_group_keys = {(row["spec_name"], row["group_value"]) for row in top_rows[:80]}
    for group in scan["groups"]:
        key = (group["spec_name"], group["group_value"])
        if key in top_group_keys:
            sample_rows.append(
                {
                    "spec_name": group["spec_name"],
                    "group_value": group["group_value"],
                    "samples": group["samples"],
                }
            )

    write_csv(output_paths["axis_capacity"], axis_rows)
    write_csv(output_paths["predicate_axis_capacity"], predicate_axis_rows)
    write_csv(output_paths["top_strata"], top_rows)
    write_jsonl(output_paths["top_strata_samples"], sample_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary, axis_rows, predicate_axis_rows), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "validation_errors": len(validation_errors),
                "selected_path": selected_path,
                "next_todo": next_todo,
                "capacity_decision": decision_payload,
                "exact_predicate_class_pair": axis_lookup(axis_rows, "exact_predicate_class_pair"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
