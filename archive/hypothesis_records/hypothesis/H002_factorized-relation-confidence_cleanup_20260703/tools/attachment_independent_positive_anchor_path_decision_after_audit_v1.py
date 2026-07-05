#!/usr/bin/env python3
"""Decide the next H002 path after the attachment positive-anchor target audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_target_independence_audit_v1"
DEFAULT_INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_path_decision_after_audit_v1"

EXPECTED_AUDIT_STATUS = "h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk"
EXPECTED_AUDIT_NEXT = "attachment_independent_positive_anchor_path_decision_after_audit_v1"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_path_decision_after_audit_v1"
STATUS_READY = "h002_attachment_independent_positive_anchor_path_decision_diagnostic_freeze"
STATUS_ERRORS = "h002_attachment_independent_positive_anchor_path_decision_input_errors"
SELECTED_PATH = "freeze_positive_anchor_target_as_diagnostic_and_move_to_compatibility_learning_plan"
NEXT_TODO = "compatibility_learning_scope_plan_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(audit: dict[str, Any], ingestion: dict[str, Any], validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit.get("status")})
    if audit.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit.get("next_todo")})
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "audit_validation_error_rows_present", "rows": len(validation_rows)})

    boundary = audit.get("boundary", {})
    required_false = [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
    ]
    for key in required_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "unexpected_boundary_split", "actual": boundary.get("split")})

    p_rel = audit.get("target_decisions", {}).get("p_rel_primary_binary", {})
    c_e = audit.get("target_decisions", {}).get("c_e_compatibility_binary", {})
    if p_rel.get("class_mass_pass") is not True:
        errors.append({"error_type": "p_rel_class_mass_not_passed", "actual": p_rel.get("class_mass_pass")})
    if p_rel.get("strict_clear_slice_count") != 0 or p_rel.get("diagnostic_clear_slice_count") != 0:
        errors.append(
            {
                "error_type": "p_rel_unexpected_clear_slice",
                "strict": p_rel.get("strict_clear_slice_count"),
                "diagnostic": p_rel.get("diagnostic_clear_slice_count"),
            }
        )
    if c_e.get("strict_clear_slice_count") != 0 or c_e.get("diagnostic_clear_slice_count") != 0:
        errors.append(
            {
                "error_type": "c_e_unexpected_clear_slice",
                "strict": c_e.get("strict_clear_slice_count"),
                "diagnostic": c_e.get("diagnostic_clear_slice_count"),
            }
        )

    if ingestion.get("validation_errors") not in (0, None):
        errors.append({"error_type": "ingestion_validation_errors_present", "actual": ingestion.get("validation_errors")})
    if ingestion.get("counts", {}).get("rows") not in (560, None):
        errors.append({"error_type": "unexpected_ingestion_row_count", "actual": ingestion.get("counts", {}).get("rows")})
    return errors


def int_field(row: dict[str, str], key: str) -> int:
    value = row.get(key, "")
    if value in ("", None):
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def summarize_slices(slice_rows: list[dict[str, str]]) -> dict[str, Any]:
    p_rel_rows = [row for row in slice_rows if row.get("target") == "p_rel_primary_binary"]
    sorted_rows = sorted(
        p_rel_rows,
        key=lambda row: (
            int_field(row, "strict_clear"),
            int_field(row, "diagnostic_clear"),
            int_field(row, "min_class_count"),
            int_field(row, "rows"),
        ),
        reverse=True,
    )
    same_visible = next((row for row in p_rel_rows if row.get("slice_name") == "same_visible_pair"), {})
    same_pred_visible = next((row for row in p_rel_rows if row.get("slice_name") == "same_predicate_visible_pair"), {})
    construction_endpoint = next((row for row in p_rel_rows if row.get("slice_name") == "construction_endpoint_strict"), {})
    return {
        "p_rel_slice_rows": len(p_rel_rows),
        "best_p_rel_slices": sorted_rows[:8],
        "same_visible_pair_rows": int_field(same_visible, "rows"),
        "same_visible_pair_min_class": int_field(same_visible, "min_class_count"),
        "same_predicate_visible_pair_rows": int_field(same_pred_visible, "rows"),
        "construction_endpoint_strict_rows": int_field(construction_endpoint, "rows"),
    }


def summarize_risks(risk_rows: list[dict[str, str]]) -> dict[str, Any]:
    by_target = Counter(row.get("target", "") for row in risk_rows)
    by_category = Counter(row.get("predictor_category", "") for row in risk_rows)
    p_rel = [row for row in risk_rows if row.get("target") == "p_rel_primary_binary"]
    top_p_rel = sorted(
        p_rel,
        key=lambda row: (
            float(row.get("majority_rule_accuracy") or 0.0) - float(row.get("majority_baseline_accuracy") or 0.0),
            float(row.get("normalized_mutual_information") or 0.0),
        ),
        reverse=True,
    )[:15]
    return {
        "risk_flags": len(risk_rows),
        "risk_flags_by_target": dict(sorted(by_target.items())),
        "risk_flags_by_category": dict(sorted(by_category.items())),
        "top_p_rel_risk_flags": top_p_rel,
    }


def build_route_table(audit: dict[str, Any], slice_summary: dict[str, Any]) -> list[dict[str, Any]]:
    p_rel = audit["target_decisions"]["p_rel_primary_binary"]
    counts = audit["counts"]
    return [
        {
            "route": "run_posterior_smoke_now",
            "verdict": "reject",
            "evidence": (
                f"class mass passes with {p_rel['class_counts']}, but strict/diagnostic clear slices are "
                f"{p_rel['strict_clear_slice_count']}/{p_rel['diagnostic_clear_slice_count']} and "
                f"full risk flags are {counts['full_risk_flags']}."
            ),
            "reason": "A posterior smoke would mainly test shortcut recovery, not factorized reliability.",
            "next_action": "keep_posterior_blocked",
        },
        {
            "route": "repair_current_560_by_selecting_controlled_slice",
            "verdict": "reject_as_immediate_path",
            "evidence": (
                f"same-visible-pair slice has {slice_summary['same_visible_pair_rows']} rows; "
                f"same-predicate-visible-pair slice has {slice_summary['same_predicate_visible_pair_rows']} rows; "
                f"construction-endpoint-strict slice has {slice_summary['construction_endpoint_strict_rows']} rows."
            ),
            "reason": "The current 560-row set does not contain enough controlled mixed strata for primary p_rel/C_e.",
            "next_action": "do_not_train_from_current_slice",
        },
        {
            "route": "mine_more_positive_anchors_with_same_policy",
            "verdict": "reject",
            "evidence": "Positive-anchor mining repaired class mass but left the same target-identifiability blocker.",
            "reason": "More rows from the same policy are likely to add volume without changing the shortcut mechanism.",
            "next_action": "only_reconsider_with_new_provenance_or_new_evidence_axis",
        },
        {
            "route": "relax_abstain_or_accept_policy",
            "verdict": "reject",
            "evidence": "Current positives already reach the predeclared minimum exactly; remaining blocker is not class mass.",
            "reason": "Changing labels to fit the posterior would weaken the reliability claim.",
            "next_action": "keep_label_policy_strict",
        },
        {
            "route": "promote_attachment_positive_anchor_target_to_paper_reliability_gt",
            "verdict": "reject",
            "evidence": "No target-independent controlled slice cleared; hidden and visible shortcuts remain predictive.",
            "reason": "The target is useful diagnostically but not independent enough for a paper-level reliability GT.",
            "next_action": "mark_attachment_target_diagnostic_only",
        },
        {
            "route": "use_attachment_packets_for_qe_and_failure_taxonomy",
            "verdict": "select_secondary",
            "evidence": "All 560 packets are materialized and visible-packet labels separate accept/reject/abstain reasons.",
            "reason": "The packet set can still teach observability, evidence sufficiency, and hard-relation failure modes.",
            "next_action": "retain_as_diagnostic_qe_observability_artifact",
        },
        {
            "route": SELECTED_PATH,
            "verdict": "selected",
            "evidence": "Target-first attachment p_rel repair has now failed after proxy, independent audit, and positive-anchor repair.",
            "reason": "The defensible H002 route is to stop treating this target as final reliability GT and return to method-level compatibility learning with explicit provenance tiers.",
            "next_action": NEXT_TODO,
        },
    ]


def build_report(summary: dict[str, Any], route_table: list[dict[str, Any]]) -> str:
    audit = summary["audit_snapshot"]
    p_rel = audit["p_rel_primary_binary"]
    risk = summary["risk_summary"]
    lines = [
        "# H002 Attachment Positive-Anchor Path Decision After Audit V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"posterior_smoke_allowed = {summary['posterior_smoke_allowed']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Input Audit Snapshot",
        "",
        "```text",
        f"rows = {audit['rows']}",
        f"p_rel_primary_binary = {p_rel['class_counts']} with min_class {p_rel['min_class_count']}",
        f"p_rel_class_mass_pass = {p_rel['class_mass_pass']}",
        f"p_rel_strict_clear_slice_count = {p_rel['strict_clear_slice_count']}",
        f"p_rel_diagnostic_clear_slice_count = {p_rel['diagnostic_clear_slice_count']}",
        f"full_risk_flags = {audit['full_risk_flags']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "Risk categories:",
        "",
        "```text",
        json.dumps(risk["risk_flags_by_category"], ensure_ascii=False, sort_keys=True),
        "```",
        "",
        "## Route Decision",
        "",
        "| Route | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for row in route_table:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Positive-anchor mining solved the class-mass problem, but not target identifiability. The",
            "current attachment target should not be used to train or promote a reliability posterior.",
            "The useful artifact is now diagnostic: it exposes which visual/mesh evidence and",
            "observability patterns are hard for attachment-like relations.",
            "",
            "The next H002 step should shift from more target repair to a method-level compatibility",
            "learning scope plan. That plan should specify which relation families and positive/negative",
            "tiers can support `C_e`, where attachment remains a diagnostic or optional hard family, and",
            "which evidence axes are allowed for `G_e` and `Q_e`.",
            "",
            "## Boundary",
            "",
            "- Train-only H002 artifact.",
            "- No validation/test usage.",
            "- No posterior training.",
            "- No paper-level reliability GT promotion.",
            "- Hidden/source/proxy fields remain diagnostic controls only.",
            "- H001 artifacts are not modified.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    audit_summary = read_json(args.audit_dir / "summary.json")
    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    validation_rows = read_jsonl(args.audit_dir / "validation_errors.jsonl")
    slice_rows = read_csv(args.audit_dir / "slice_audit.csv")
    risk_rows = read_csv(args.audit_dir / "full_predictor_risk_flags.csv")

    errors = validate_inputs(audit_summary, ingestion_summary, validation_rows)
    slice_summary = summarize_slices(slice_rows)
    risk_summary = summarize_risks(risk_rows)
    route_table = build_route_table(audit_summary, slice_summary)

    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_attachment_positive_anchor_path_decision_inputs"
    selected_path = SELECTED_PATH if not errors else "fix_inputs_before_path_decision"

    p_rel = audit_summary["target_decisions"]["p_rel_primary_binary"]
    c_e = audit_summary["target_decisions"]["c_e_compatibility_binary"]
    p_obs = audit_summary["target_decisions"]["p_obs_primary_binary"]
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_roots": {
            "audit": rel_path(args.audit_dir),
            "ingestion": rel_path(args.ingestion_dir),
        },
        "validation_errors": len(errors),
        "selected_path": selected_path,
        "next_todo": next_todo,
        "posterior_smoke_allowed": False,
        "attachment_positive_anchor_target_status": "diagnostic_only",
        "paper_evidence_allowed": False,
        "audit_snapshot": {
            "rows": audit_summary["counts"]["rows"],
            "full_risk_flags": audit_summary["counts"]["full_risk_flags"],
            "strict_clear_slices_total": audit_summary["counts"]["strict_clear_slices_total"],
            "diagnostic_clear_slices_total": audit_summary["counts"]["diagnostic_clear_slices_total"],
            "p_rel_primary_binary": {
                "rows": p_rel["rows"],
                "class_counts": p_rel["class_counts"],
                "min_class_count": p_rel["min_class_count"],
                "class_mass_pass": p_rel["class_mass_pass"],
                "strict_clear_slice_count": p_rel["strict_clear_slice_count"],
                "diagnostic_clear_slice_count": p_rel["diagnostic_clear_slice_count"],
            },
            "c_e_compatibility_binary": {
                "rows": c_e["rows"],
                "class_counts": c_e["class_counts"],
                "min_class_count": c_e["min_class_count"],
                "class_mass_pass": c_e["class_mass_pass"],
                "strict_clear_slice_count": c_e["strict_clear_slice_count"],
                "diagnostic_clear_slice_count": c_e["diagnostic_clear_slice_count"],
            },
            "p_obs_primary_binary": {
                "rows": p_obs["rows"],
                "class_counts": p_obs["class_counts"],
                "min_class_count": p_obs["min_class_count"],
                "class_mass_pass": p_obs["class_mass_pass"],
                "strict_clear_slice_count": p_obs["strict_clear_slice_count"],
                "diagnostic_clear_slice_count": p_obs["diagnostic_clear_slice_count"],
            },
        },
        "slice_summary": slice_summary,
        "risk_summary": risk_summary,
        "route_table": route_table,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "hidden_fields_as_model_input": False,
            "source_proxy_fields_as_model_input": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "path_decision": rel_path(args.output_dir / "path_decision.json"),
            "route_table": rel_path(args.output_dir / "route_table.csv"),
            "top_risk_flags": rel_path(args.output_dir / "top_risk_flags.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    path_decision = {
        "selected_path": selected_path,
        "next_todo": next_todo,
        "posterior_smoke_allowed": False,
        "attachment_positive_anchor_target_status": "diagnostic_only",
        "route_table": route_table,
        "rationale": {
            "class_mass_repaired": True,
            "target_independence_repaired": False,
            "why_not_more_same_mining": "The failure mechanism is shortcut identifiability, not remaining positive count.",
            "why_not_label_relaxation": "Relaxation would tune the target to the model rather than provide independent evidence.",
            "what_survives": [
                "attachment visual/mesh packet set as Q_e and failure-taxonomy evidence",
                "attachment candidate rows as diagnostic hard-family examples",
                "counterfactual construction lessons for future C_e training",
            ],
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "path_decision.json", path_decision)
    write_csv(args.output_dir / "route_table.csv", route_table)
    write_csv(args.output_dir / "top_risk_flags.csv", risk_summary["top_p_rel_risk_flags"])
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary, route_table), encoding="utf-8")

    print(f"status={status}")
    print(f"selected_path={selected_path}")
    print(f"next={next_todo}")
    print(f"posterior_smoke_allowed={False}")
    print(f"validation_errors={len(errors)}")


if __name__ == "__main__":
    main()
