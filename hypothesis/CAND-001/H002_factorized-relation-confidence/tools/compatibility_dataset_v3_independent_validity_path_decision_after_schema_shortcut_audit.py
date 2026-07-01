#!/usr/bin/env python3
"""Decide the next path after independent-validity shortcut audit blocked smoke."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_schema_shortcut_audit"
DEFAULT_CANDIDATE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit"
)

EXPECTED_AUDIT_STATUS = "h002_compatibility_dataset_v3_independent_validity_schema_shortcut_audit_blocked_shortcut_risk"
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_path_decision_select_stratum_repair_capacity_scan"
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_path_decision_input_errors"
SELECTED_PATH = "freeze_current_target_diagnostic_select_full_train_stratum_repair_capacity_scan"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan"

MIN_REPAIRED_PRIMARY_ROWS = 800
MIN_REPAIRED_PER_CLASS = 400


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = row
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def value_key(value: Any) -> str:
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def primary_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in candidate_rows if row.get("labels", {}).get("primary_binary_usable") is True]


def validate_inputs(audit: dict[str, Any], validation_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit.get("status")})
    if audit.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next", "actual": audit.get("next_todo")})
    # The blocked audit intentionally records one validation row for shortcut risk.
    if audit.get("validation_errors") != 1:
        errors.append({"error_type": "unexpected_audit_validation_error_count", "actual": audit.get("validation_errors")})
    if len(validation_rows) != 1:
        errors.append({"error_type": "unexpected_validation_rows", "actual": len(validation_rows)})
    risk = audit.get("risk_summary", {})
    expected_blockers = {"subject_object_class_pair", "predicate_x_class_pair"}
    actual_blockers = set(risk.get("allowed_feature_high_or_medium_probe_names", []))
    if not expected_blockers.issubset(actual_blockers):
        errors.append({"error_type": "missing_expected_shortcut_blockers", "actual": sorted(actual_blockers)})
    if risk.get("sanitized_blocked_feature_path_hits") != 0:
        errors.append({"error_type": "sanitized_feature_path_leakage", "actual": risk.get("sanitized_blocked_feature_path_hits")})
    if risk.get("sanitized_blocked_field_leakage_hits") != 0:
        errors.append({"error_type": "sanitized_field_leakage", "actual": risk.get("sanitized_blocked_field_leakage_hits")})
    counts = audit.get("counts", {})
    if counts.get("primary_binary_rows") != 3200 or counts.get("sanitized_primary_rows") != 3200:
        errors.append({"error_type": "unexpected_primary_counts", "counts": counts})
    if len(primary_rows(candidate_rows)) != 3200:
        errors.append({"error_type": "unexpected_candidate_primary_rows", "actual": len(primary_rows(candidate_rows))})

    boundary = audit.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed", "runs_learned_smoke"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def axis_capacity(
    rows: list[dict[str, Any]],
    axis_name: str,
    axis_fn: Callable[[dict[str, Any]], Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        label = int(row["labels"]["primary_binary"])
        groups[value_key(axis_fn(row))][label] += 1
    mixed = {key: counter for key, counter in groups.items() if counter[0] > 0 and counter[1] > 0}
    balanced_capacity = sum(2 * min(counter[0], counter[1]) for counter in mixed.values())
    top_groups = []
    for key, counter in sorted(mixed.items(), key=lambda kv: (min(kv[1][0], kv[1][1]), sum(kv[1].values())), reverse=True)[:25]:
        top_groups.append(
            {
                "axis": axis_name,
                "stratum": key,
                "positive": counter[1],
                "negative": counter[0],
                "balanced_capacity": 2 * min(counter[0], counter[1]),
                "rows": sum(counter.values()),
            }
        )
    summary = {
        "axis": axis_name,
        "groups": len(groups),
        "mixed_groups": len(mixed),
        "balanced_capacity": balanced_capacity,
        "balanced_positive_capacity": balanced_capacity // 2,
        "balanced_negative_capacity": balanced_capacity // 2,
        "meets_repair_minimum": balanced_capacity >= MIN_REPAIRED_PRIMARY_ROWS,
        "reason": (
            "enough_capacity_for_repair_preview"
            if balanced_capacity >= MIN_REPAIRED_PRIMARY_ROWS
            else "insufficient_balanced_capacity_in_current_artifact"
        ),
    }
    return summary, top_groups


def repair_capacity_tables(candidate_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = primary_rows(candidate_rows)
    axis_specs: list[tuple[str, Callable[[dict[str, Any]], Any]]] = [
        ("family", lambda row: row["family"]),
        ("predicate_label", lambda row: nested_get(row, "feature_blocks.T_e.predicate_label")),
        (
            "subject_object_class_pair",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
        ),
        (
            "predicate_x_class_pair",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.predicate_label"),
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
            ),
        ),
        (
            "predicate_x_class_pair_x_rank_band",
            lambda row: (
                nested_get(row, "feature_blocks.T_e.predicate_label"),
                nested_get(row, "feature_blocks.T_e.subject_class_label"),
                nested_get(row, "feature_blocks.T_e.object_class_label"),
                nested_get(row, "feature_blocks.Z_e_safe.rank_band"),
            ),
        ),
    ]
    summaries: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for axis, fn in axis_specs:
        summary, top = axis_capacity(rows, axis, fn)
        summaries.append(summary)
        top_rows.extend(top)
    return summaries, top_rows


def key_probe_rows(shortcut_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    wanted = {
        "predicate_x_class_pair",
        "subject_object_class_pair",
        "predicate_label",
        "semantic_score_norm",
        "blocked_G_e_summary.geometry_status",
        "blocked_G_e_summary.consistency_score",
        "blocked_G_e_summary.geometry_residual_proxy",
        "blocked_G_e_summary.p_geom_valid",
    }
    rows: list[dict[str, Any]] = []
    for row in shortcut_rows:
        if row.get("probe_name") in wanted:
            rows.append(
                {
                    "probe_name": row.get("probe_name"),
                    "source": row.get("source"),
                    "allowed_feature": row.get("allowed_feature"),
                    "accuracy": float(row.get("accuracy") or 0.0),
                    "risk_level": row.get("risk_level"),
                    "decision_role": (
                        "blocking_allowed_shortcut"
                        if row.get("allowed_feature") == "True" and row.get("risk_level") in {"high", "medium"}
                        else "blocked_or_diagnostic"
                    ),
                }
            )
    return rows


def route_rows(repair_capacity: list[dict[str, Any]], audit: dict[str, Any]) -> list[dict[str, Any]]:
    by_axis = {row["axis"]: row for row in repair_capacity}
    exact_cap = by_axis["predicate_x_class_pair"]["balanced_capacity"]
    class_pair_cap = by_axis["subject_object_class_pair"]["balanced_capacity"]
    return [
        {
            "route": "run_learned_smoke_now",
            "verdict": "reject",
            "evidence": "Allowed sanitized probes still recover the target: predicate_x_class_pair = 0.976562, subject_object_class_pair = 0.84.",
            "reason": "A learned model would likely exploit object-pair/predicate-pair strata instead of learning C_e.",
            "next_action": "keep_learned_smoke_blocked",
        },
        {
            "route": "use_current_sanitized_view_but_drop_object_labels",
            "verdict": "reject",
            "evidence": "Dropping object labels would hide the observed bias but would also remove part of T_e.",
            "reason": "H002's semantic factor includes object class semantics; removing it would test a weakened method.",
            "next_action": "do_not_repair_by_feature_deletion_only",
        },
        {
            "route": "use_current_artifact_with_exact_predicate_class_rebalancing",
            "verdict": "reject",
            "evidence": f"Exact predicate x class-pair balanced capacity is only {exact_cap} rows.",
            "reason": f"The predeclared repair minimum is {MIN_REPAIRED_PRIMARY_ROWS} rows and {MIN_REPAIRED_PER_CLASS} per class.",
            "next_action": "current_artifact_repair_not_enough",
        },
        {
            "route": "use_current_artifact_with_class_pair_only_rebalancing",
            "verdict": "reject",
            "evidence": f"Class-pair balanced capacity is {class_pair_cap} rows, but predicate_x_class_pair remains the high-risk probe.",
            "reason": "Balancing only subject/object class would not control the strongest shortcut.",
            "next_action": "do_not_ignore_predicate_conditioning",
        },
        {
            "route": "treat_geometry_status_or_p_geom_valid_as_main_input",
            "verdict": "reject",
            "evidence": "Blocked construction summaries recover the target almost perfectly; geometry_status/consistency/residual are target-construction summaries.",
            "reason": "Using them as learned inputs would collapse the task to the rule that built the label.",
            "next_action": "keep_only_as blocked diagnostic or baseline outside learned C_e input",
        },
        {
            "route": "freeze_current_independent_validity_as_diagnostic",
            "verdict": "selected_as_boundary",
            "evidence": "The artifact proves that GT-anchored validity alone does not guarantee target identifiability.",
            "reason": "This is useful negative evidence, but not a smoke-ready reliability target.",
            "next_action": "record_as_diagnostic_not_paper_claim",
        },
        {
            "route": "full_train_stratum_repair_capacity_scan",
            "verdict": "selected_next",
            "evidence": "Current artifact lacks exact predicate-class mixed capacity, but full train has much larger source pools than the sampled 4027 rows.",
            "reason": "Before abandoning independent validity, check whether full train can create exact predicate x class-pair controlled positives/negatives.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "promote_to_paper_reliability_evidence",
            "verdict": "reject",
            "evidence": f"audit status is {audit.get('status')} and learned smoke is blocked.",
            "reason": "This remains hypothesis-stage diagnostic evidence only.",
            "next_action": "do_not_promote",
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Scan full train rows for exact predicate x subject/object class strata that contain both positive and negative independent-validity candidates.",
        "required_controls": [
            "exact predicate label match within each stratum",
            "exact subject/object class pair match within each stratum",
            "balanced accept/reject within each retained stratum",
            "no geometry_status, p_geom_valid, consistency_score, or residual as model input",
            "rank-band and scan caps after exact semantic-stratum balance",
            "no validation/test usage",
        ],
        "success_gates": [
            f"at least {MIN_REPAIRED_PRIMARY_ROWS} balanced primary rows",
            f"at least {MIN_REPAIRED_PER_CLASS} rows per binary class",
            "allowed semantic-stratum probes below medium risk after materialization",
            "raw G_e features remain available and construction summaries remain blocked",
        ],
        "fallback_if_capacity_fails": "freeze independent validity as diagnostic and continue H002 around scoped C_e mechanism plus future external/human reliability target.",
    }


def build_summary(
    audit: dict[str, Any],
    input_errors: list[dict[str, Any]],
    repair_capacity: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    status = STATUS_ERRORS if input_errors else STATUS_READY
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_path_decision",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_audit_status": audit.get("status"),
        "input_audit_validation_errors": audit.get("validation_errors"),
        "next_todo": "fix_independent_validity_path_decision_inputs" if input_errors else NEXT_TODO,
        "output_paths": {
            "claim_boundary": rel_path(output_dir / "claim_boundary.json"),
            "key_probe_table": rel_path(output_dir / "key_probe_table.csv"),
            "next_plan_contract": rel_path(output_dir / "next_plan_contract.json"),
            "repair_capacity_table": rel_path(output_dir / "repair_capacity_table.csv"),
            "repair_top_strata": rel_path(output_dir / "repair_top_strata.csv"),
            "report": rel_path(output_dir / "report.md"),
            "route_table": rel_path(output_dir / "route_table.csv"),
            "summary": rel_path(output_dir / "summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "repair_decision": {
            "current_artifact_exact_predicate_class_repair_feasible": next(
                row for row in repair_capacity if row["axis"] == "predicate_x_class_pair"
            )["meets_repair_minimum"],
            "selected_path": SELECTED_PATH,
            "selected_next": NEXT_TODO,
        },
        "route_verdicts": {row["route"]: row["verdict"] for row in routes},
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH if not input_errors else "fix_inputs",
        "status": status,
        "validation_errors": len(input_errors),
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "accepted_claims": [
            "The current independent-validity materialization is useful as a diagnostic target-identifiability artifact.",
            "The schema audit shows construction summaries must be excluded from learned C_e inputs.",
        ],
        "blocked_claims": [
            "Do not claim an independent reliability target is ready.",
            "Do not run or report learned smoke on the current independent-validity target.",
            "Do not claim p_rel/p_obs reliability improvement from this artifact.",
            "Do not promote this artifact to paper evidence.",
        ],
        "still_viable_direction": [
            "Full-train exact semantic-stratum repair may still make an independent validity target possible.",
            "Previously passed relative_vertical and support/contact pose-conditioned same-G C_e results remain scoped mechanism evidence.",
        ],
    }


def build_report(summary: dict[str, Any], repair_capacity: list[dict[str, Any]], key_probes: list[dict[str, Any]]) -> str:
    exact = next(row for row in repair_capacity if row["axis"] == "predicate_x_class_pair")
    class_pair = next(row for row in repair_capacity if row["axis"] == "subject_object_class_pair")
    lines = [
        "# H002 Independent Validity Path Decision After Schema Shortcut Audit",
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
        "## Decision",
        "",
        "The current independent-validity target is frozen as diagnostic evidence, not promoted to learned smoke.",
        "The next step is a full-train stratum-repair capacity scan.",
        "",
        "## Why Learned Smoke Is Blocked",
        "",
        "| Probe | Accuracy | Risk |",
        "| --- | ---: | --- |",
    ]
    for row in key_probes:
        if row["probe_name"] in {"predicate_x_class_pair", "subject_object_class_pair"}:
            lines.append(f"| `{row['probe_name']}` | {row['accuracy']:.6f} | `{row['risk_level']}` |")
    lines.extend(
        [
            "",
            "## Current Artifact Repair Capacity",
            "",
            "| Control Axis | Groups | Mixed Groups | Balanced Capacity | Verdict |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in repair_capacity:
        lines.append(
            f"| `{row['axis']}` | {row['groups']} | {row['mixed_groups']} | {row['balanced_capacity']} | `{row['reason']}` |"
        )
    lines.extend(
        [
            "",
            "Key point:",
            "",
            "```text",
            f"predicate_x_class_pair_balanced_capacity = {exact['balanced_capacity']}",
            f"subject_object_class_pair_balanced_capacity = {class_pair['balanced_capacity']}",
            "```",
            "",
            "Exact predicate-class repair is the necessary control because `predicate_x_class_pair` is the strongest allowed shortcut. "
            "The current artifact has only 150 balanced rows under that control, so resampling the current artifact is not enough.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit = read_json(args.audit_dir / "summary.json")
    validation_rows = read_jsonl(args.audit_dir / "validation_errors.jsonl")
    shortcut_rows = read_csv(args.audit_dir / "shortcut_probes.csv")
    candidate_rows = read_jsonl(args.candidate_dir / "candidate_rows.jsonl")

    input_errors = validate_inputs(audit, validation_rows, candidate_rows)
    repair_capacity, repair_top_strata = repair_capacity_tables(candidate_rows)
    key_probes = key_probe_rows(shortcut_rows)
    routes = route_rows(repair_capacity, audit)
    summary = build_summary(audit, input_errors, repair_capacity, routes, args.output_dir)

    write_csv(args.output_dir / "repair_capacity_table.csv", repair_capacity)
    write_csv(args.output_dir / "repair_top_strata.csv", repair_top_strata)
    write_csv(args.output_dir / "key_probe_table.csv", key_probes)
    write_csv(args.output_dir / "route_table.csv", routes)
    write_json(args.output_dir / "claim_boundary.json", claim_boundary())
    write_json(args.output_dir / "next_plan_contract.json", next_plan_contract())
    write_jsonl(args.output_dir / "validation_errors.jsonl", input_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(build_report(summary, repair_capacity, key_probes), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_path": summary["selected_path"],
                "next_todo": summary["next_todo"],
                "validation_errors": len(input_errors),
                "predicate_x_class_pair_capacity": next(
                    row for row in repair_capacity if row["axis"] == "predicate_x_class_pair"
                )["balanced_capacity"],
            },
            sort_keys=True,
        )
    )
    return 1 if input_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
