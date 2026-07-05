#!/usr/bin/env python3
"""Decide the H002 path after close-by schema/shortcut audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit"
DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_proximity_close_by_path_decision_input_errors"
SELECTED_PATH = "freeze_close_by_diagnostic_select_support_contact_individual_predicate_probe"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_probe_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(
    audit_summary: dict[str, Any],
    risk_summary: dict[str, Any],
    audit_dir: Path,
    capacity_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append(
            {
                "error_type": "unexpected_audit_status",
                "expected": EXPECTED_AUDIT_STATUS,
                "actual": audit_summary.get("status"),
            }
        )
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append(
            {
                "error_type": "unexpected_audit_next_todo",
                "expected": EXPECTED_AUDIT_NEXT,
                "actual": audit_summary.get("next_todo"),
            }
        )
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("learned_smoke_allowed") is not False:
        errors.append(
            {"error_type": "learned_smoke_unexpectedly_allowed", "actual": audit_summary.get("learned_smoke_allowed")}
        )
    if audit_summary.get("main_claim_verdict") != "blocked_for_close_by_current_target":
        errors.append(
            {"error_type": "unexpected_main_claim_verdict", "actual": audit_summary.get("main_claim_verdict")}
        )
    if audit_summary.get("critical_blockers", 0) < 1:
        errors.append({"error_type": "missing_critical_blockers", "actual": audit_summary.get("critical_blockers")})

    if risk_summary.get("schema_leakage_passed") is not True:
        errors.append({"error_type": "schema_leakage_not_passed", "actual": risk_summary.get("schema_leakage_passed")})
    if risk_summary.get("learned_smoke_allowed") is not False:
        errors.append(
            {
                "error_type": "risk_summary_learned_smoke_unexpectedly_allowed",
                "actual": risk_summary.get("learned_smoke_allowed"),
            }
        )
    critical_blockers = risk_summary.get("critical_blockers", [])
    if not critical_blockers:
        errors.append({"error_type": "risk_summary_missing_critical_blockers"})
    blocker_names = {row.get("blocker") for row in critical_blockers}
    for required in [
        "primary_binary:normalized_distance_xy",
        "primary_binary:normalized_distance_3d",
        "primary_binary:p_geom_valid_rule",
    ]:
        if required not in blocker_names:
            errors.append({"error_type": "missing_required_blocker", "blocker": required})

    boundary = audit_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_learned_smoke",
        "trains_new_model",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_not_false", "key": key, "actual": boundary.get(key)})

    for name in ["summary.json", "risk_summary.json", "shortcut_probes.csv", "schema_leakage.csv"]:
        if not (audit_dir / name).exists():
            errors.append({"error_type": "missing_audit_artifact", "path": rel_path(audit_dir / name)})
    for name in ["summary.json", "predicate_capacity.csv"]:
        if not (capacity_dir / name).exists():
            errors.append({"error_type": "missing_capacity_artifact", "path": rel_path(capacity_dir / name)})
    return errors


def parse_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def capacity_for(predicates: list[str], capacity_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_predicate = {row["predicate_label"]: row for row in capacity_rows}
    out: list[dict[str, Any]] = []
    for predicate in predicates:
        row = by_predicate.get(predicate, {})
        if not row:
            out.append(
                {
                    "predicate_label": predicate,
                    "priority": "",
                    "role": "missing_capacity_row",
                    "open3dsg_train_full_gt_count": 0,
                    "queue_rows": 0,
                    "exact_matches": 0,
                    "mixed_class_pair_groups_exact_vs_other": 0,
                    "balanced_rows_exact_vs_other": 0,
                    "verdict": "blocked_missing_capacity_row",
                    "reason": "predicate was not found in the capacity scan artifact",
                }
            )
            continue
        out.append(
            {
                "predicate_label": predicate,
                "family": row.get("family", ""),
                "priority": "",
                "role": "",
                "open3dsg_train_full_gt_count": parse_int(row.get("open3dsg_train_full_gt_count")),
                "queue_rows": parse_int(row.get("queue_rows")),
                "hl_rows": parse_int(row.get("hl_rows")),
                "lh_rows": parse_int(row.get("lh_rows")),
                "exact_matches": parse_int(row.get("label_match_status_counts", "").split("exact_match:")[-1].split(";")[0])
                if "exact_match:" in row.get("label_match_status_counts", "")
                else 0,
                "mixed_class_pair_groups_exact_vs_other": parse_int(row.get("mixed_class_pair_groups_exact_vs_other")),
                "balanced_rows_exact_vs_other": parse_int(row.get("balanced_rows_exact_vs_other")),
                "source_verdict": row.get("verdict", ""),
                "source_reason": row.get("reason", ""),
            }
        )
    priority = {
        "standing on": (
            1,
            "primary_individual_probe",
            "largest exact-match support/contact candidate and enough class-pair mixing; must control floor/table/surface class shortcut",
        ),
        "lying on": (
            2,
            "secondary_pose_conditioned_probe",
            "pose-conditioned support/contact mechanism remains useful; exact count is lower than standing on but still materializable",
        ),
        "supported by": (
            3,
            "diagnostic_superordinate_probe",
            "support superordinate has lower exact count and overlaps with standing/support semantics; useful for boundary, weaker as main target",
        ),
    }
    for row in out:
        rank, role, reason = priority.get(row["predicate_label"], (99, "optional", "not prioritized"))
        row["priority"] = rank
        row["role"] = role
        row["recommended_next_action"] = reason
    return sorted(out, key=lambda row: row["priority"] if isinstance(row["priority"], int) else 99)


def close_by_verdict(audit_summary: dict[str, Any], risk_summary: dict[str, Any]) -> dict[str, Any]:
    blockers = risk_summary["critical_blockers"]
    return {
        "predicate_label": "close by",
        "family": "proximity",
        "main_claim_allowed": False,
        "learned_smoke_allowed": False,
        "diagnostic_allowed": True,
        "selected_role": "diagnostic_generality_evidence",
        "reason": (
            "The current target is schema-clean and large enough, but normalized distance and H001-style "
            "geometry-rule baselines already solve the label. A learned model would not demonstrate "
            "predicate-geometry compatibility beyond distance thresholding."
        ),
        "primary_binary_rows": audit_summary.get("row_counts", {}).get("primary_binary_rows"),
        "raw_distance_diagnostic_rows": audit_summary.get("row_counts", {}).get("raw_distance_diagnostic_rows"),
        "critical_blockers": len(blockers),
        "strongest_blockers": [
            {
                "blocker": row["blocker"],
                "accuracy": row["accuracy"],
                "auroc": row["auroc"],
            }
            for row in blockers[:5]
        ],
        "not_allowed": [
            "do not train learned smoke on the current close-by target",
            "do not use current close-by target as the main H002 claim",
            "do not report factorized posterior gain over this target without a stricter matched target",
        ],
    }


def rejected_paths() -> list[dict[str, Any]]:
    return [
        {
            "route": "run_learned_smoke_on_current_close_by_target",
            "verdict": "reject",
            "reason": "Distance and p_geom_valid baselines already solve the target, so learned smoke would be non-identifiable.",
            "allowed_future_condition": "Only if a normalized-distance-matched or otherwise shortcut-controlled close-by target is rebuilt.",
        },
        {
            "route": "use_stronger_combiner_or_neural_architecture_now",
            "verdict": "reject",
            "reason": "A stronger combiner would likely learn the same distance threshold and inflate apparent performance.",
            "allowed_future_condition": "After target identifiability is repaired and distance-only baselines no longer dominate.",
        },
        {
            "route": "promote_close_by_as_main_h002_claim",
            "verdict": "reject",
            "reason": "The target verifies proximity thresholding, not semantic-geometry compatibility learning.",
            "allowed_future_condition": "A new source/audit target where accept/reject varies within matched distance and object-context strata.",
        },
        {
            "route": "treat_no_gt_close_by_as_negative",
            "verdict": "reject",
            "reason": "No-GT close-by pairs can be reliable but unlabeled because proximity annotations are dense and incomplete.",
            "allowed_future_condition": "Only as a separately labeled reject set with visual/mesh or independent audit evidence.",
        },
        {
            "route": "search_stricter_close_by_source_immediately",
            "verdict": "defer",
            "reason": "Possible but lower priority: current artifact already shows close-by is mostly a distance-threshold family.",
            "allowed_future_condition": "Use if support/contact individual probes also fail or if a reviewer asks for proximity-specific repair.",
        },
        {
            "route": "support_contact_individual_predicate_probe",
            "verdict": "select",
            "reason": "It tests a family where geometry evidence should include contact/support structure rather than only distance.",
            "allowed_future_condition": "Proceed with predicate-specific target plan and shortcut audit before any learned smoke.",
        },
    ]


def route_decision(verdict: dict[str, Any], next_probe: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first = next_probe[0]
    return [
        {
            "decision": "freeze_close_by_current_target",
            "verdict": "selected",
            "evidence": f"{verdict['critical_blockers']} critical blockers; normalized distance reaches acc/AUROC 1.0/1.0.",
            "claim_boundary": "close by is diagnostic/generality evidence only",
        },
        {
            "decision": "do_not_run_learned_smoke",
            "verdict": "selected",
            "evidence": "distance_xy, distance_3d, normalized distance, and p_geom_valid_rule solve or nearly solve the target",
            "claim_boundary": "no p_rel/p_obs or compatibility-learning metric claim from this target",
        },
        {
            "decision": "select_next_family_probe",
            "verdict": "selected",
            "evidence": f"support/contact individual priority starts with {first['predicate_label']} ({first['queue_rows']} rows, {first['exact_matches']} exact matches)",
            "claim_boundary": "next step is target planning and shortcut audit, not paper-level evidence",
        },
    ]


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "close_by_is_too_trivial",
            "severity": "high_if_used_as_main",
            "evidence": "normalized_distance_xy and normalized_distance_3d solve primary binary with acc/AUROC 1.0/1.0",
            "response": "Do not use close by as main learned target; keep it as proximity-family diagnostic evidence.",
        },
        {
            "risk": "generality_too_narrow_without_close_by",
            "severity": "medium",
            "evidence": "close by was evaluated and explicitly failed target-identifiability due distance shortcut",
            "response": "Report close by as family taxonomy evidence, then use support/contact individual predicates for harder geometry evidence.",
        },
        {
            "risk": "support_contact_grouped_target_already_failed",
            "severity": "medium",
            "evidence": "previous grouped support/contact target was class/predicate shortcut-prone",
            "response": "Do not reuse grouped target; plan individual predicate probes with predicate-specific evidence policies.",
        },
        {
            "risk": "architecture_change_cannot_fix_bad_target",
            "severity": "high",
            "evidence": "shortcut audit blocks the target before modeling",
            "response": "Repair or change target before learned smoke; stronger fusion is secondary to target identifiability.",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], verdict: dict[str, Any], next_probe: list[dict[str, Any]]) -> None:
    blockers = verdict["strongest_blockers"]
    lines = [
        "# H002 Proximity Close-By Path Decision After Schema Shortcut Audit",
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
        "`close by` current target is frozen as diagnostic/generality evidence. Learned smoke is not allowed.",
        "",
        "Reason: current labels are solved by distance/rule geometry baselines, so a learned compatibility model would not prove the H002 factor separation.",
        "",
        "## Critical Evidence",
        "",
        "| Blocker | Accuracy | AUROC |",
        "| --- | ---: | ---: |",
    ]
    for row in blockers:
        lines.append(f"| `{row['blocker']}` | {row['accuracy']} | {row['auroc']} |")
    lines.extend(
        [
            "",
            "## Selected Next Probe",
            "",
            "Move to support/contact individual predicate probes. Do not reuse the previous grouped support/contact target.",
            "",
            "| Priority | Predicate | Role | Queue Rows | Exact Matches | Mixed Class-Pair Groups | Reason |",
            "| ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in next_probe:
        lines.append(
            "| "
            f"{row['priority']} | `{row['predicate_label']}` | {row['role']} | {row['queue_rows']} | "
            f"{row['exact_matches']} | {row['mixed_class_pair_groups_exact_vs_other']} | "
            f"{row['recommended_next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only path decision.",
            "- No validation/test usage.",
            "- No learned smoke or model training.",
            "- No new labels or row materialization.",
            "- No H001 artifact modification.",
            "- No paper-level metric evidence.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary_path = args.audit_dir / "summary.json"
    risk_summary_path = args.audit_dir / "risk_summary.json"
    capacity_path = args.capacity_dir / "predicate_capacity.csv"

    if audit_summary_path.exists() and risk_summary_path.exists():
        audit_summary = read_json(audit_summary_path)
        risk_summary = read_json(risk_summary_path)
    else:
        audit_summary = {}
        risk_summary = {}

    validation_errors = validate_inputs(audit_summary, risk_summary, args.audit_dir, args.capacity_dir)
    capacity_rows = read_csv(capacity_path) if capacity_path.exists() else []

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_AUDIT_NEXT
        verdict: dict[str, Any] = {}
        next_probe: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        routes: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO
        verdict = close_by_verdict(audit_summary, risk_summary)
        next_probe = capacity_for(["standing on", "lying on", "supported by"], capacity_rows)
        rejected = rejected_paths()
        routes = route_decision(verdict, next_probe)
        risks = reviewer_risks()

    summary = {
        "boundary": {
            "fills_labels": False,
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
        "input_paths": {
            "audit_summary": rel_path(audit_summary_path),
            "risk_summary": rel_path(risk_summary_path),
            "capacity_scan_predicate_capacity": rel_path(capacity_path),
        },
        "next_todo": next_todo,
        "output_paths": {
            "close_by_verdict": rel_path(args.output_dir / "close_by_verdict.json"),
            "next_probe_plan": rel_path(args.output_dir / "next_probe_plan.csv"),
            "rejected_paths": rel_path(args.output_dir / "rejected_paths.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "reviewer_risk_table": rel_path(args.output_dir / "reviewer_risk_table.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "close_by_verdict.json", verdict)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_csv(args.output_dir / "rejected_paths.csv", rejected)
    write_csv(args.output_dir / "next_probe_plan.csv", next_probe)
    write_csv(args.output_dir / "reviewer_risk_table.csv", risks)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_report(args.output_dir / "report.md", summary, verdict, next_probe)

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
