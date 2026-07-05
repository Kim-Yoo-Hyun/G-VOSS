#!/usr/bin/env python3
"""Decide path after R7 class-pair repair schema shortcut audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit"
)
DEFAULT_INGESTION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion"
)
DEFAULT_CAPACITY_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_schema_shortcut_audit_blocked_shortcut_risk"
)
EXPECTED_AUDIT_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit"
)
EXPECTED_INGESTION_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingested_ready_for_schema_shortcut_audit"
)
EXPECTED_CAPACITY_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_freeze_diagnostic"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_input_errors"
)
SELECTED_PATH = (
    "freeze_r7_class_pair_repair_as_diagnostic_select_scope_synthesis"
)
NEXT_TODO = "compatibility_dataset_v3_scope_synthesis_after_attachment_observability_diagnostic_freeze"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
    ingestion_summary: dict[str, Any],
    capacity_summary: dict[str, Any],
    audit_dir: Path,
    ingestion_dir: Path,
    capacity_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("learned_smoke_allowed") is not False:
        errors.append({"error_type": "audit_unexpectedly_allows_smoke", "actual": audit_summary.get("learned_smoke_allowed")})
    if audit_summary.get("counts", {}).get("allowed_high_risk_blockers", 0) < 1:
        errors.append(
            {
                "error_type": "missing_shortcut_blocker",
                "actual": audit_summary.get("counts", {}).get("allowed_high_risk_blockers"),
            }
        )

    if ingestion_summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "actual": ingestion_summary.get("status")})
    if capacity_summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity_summary.get("status")})

    for summary_name, summary in [
        ("audit", audit_summary),
        ("ingestion", ingestion_summary),
        ("capacity", capacity_summary),
    ]:
        boundary = summary.get("boundary", {})
        for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
            if boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": f"{summary_name}_boundary_not_false",
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )

    for path in [
        audit_dir / "summary.json",
        audit_dir / "shortcut_audit.csv",
        audit_dir / "controlled_strata_capacity.csv",
        audit_dir / "route_decision.csv",
        ingestion_dir / "summary.json",
        capacity_dir / "summary.json",
    ]:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel_path(path)})
    if (audit_dir / "validation_errors.jsonl").exists() and (audit_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors"})
    return errors


def find_capacity(capacity_rows: list[dict[str, str]], target_name: str, axis_name: str) -> dict[str, str]:
    for row in capacity_rows:
        if row.get("target_name") == target_name and row.get("axis_name") == axis_name:
            return row
    return {"target_name": target_name, "axis_name": axis_name, "missing": "true"}


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# R7 Attachment Observability Class-Pair Repair Path Decision",
        "",
        "## Result",
        "",
        "```text",
        f"artifact_root = {summary['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "Freeze the current R7 class-pair repair artifact as diagnostic evidence.",
        "Do not run learned smoke, calibrated `p_rel`, or calibrated `p_obs` on this artifact.",
        "",
        "The blocker is not row count. The current artifact has combined observable `p_rel`",
        "`258/90` and `hanging on` `86/90`, but the target is explained by visible",
        "object-class and class-pair priors.",
        "",
        "## Key Evidence",
        "",
        "- combined `p_rel`: `predicate_subject_object_class_pair` majority accuracy `1.0`",
        "- `hanging on` `p_rel`: `subject_label` / `subject_object_class_pair` majority accuracy `1.0`",
        "- `attached to` `p_rel`: single-class `172/0`",
        "- `p_obs`: negative-sparse `455/25`",
        "- exact predicate-class-pair mixed capacity after visible labels: `0`",
        "",
        "## Selected Path",
        "",
        "`freeze_r7_class_pair_repair_as_diagnostic_select_scope_synthesis`",
        "",
        "R7 remains part of the H002 route taxonomy as an observability-heavy relation",
        "family, but the current class-pair repair target is not a main learned target.",
        "",
        "## Boundary",
        "",
        "- train-only path decision",
        "- no validation/test usage",
        "- no H001 artifact modification",
        "- no new labels",
        "- no row materialization",
        "- no learned smoke or model training",
        "- no paper-level evidence claim",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    capacity_summary = read_json(args.capacity_dir / "summary.json")
    capacity_rows = read_csv(args.audit_dir / "controlled_strata_capacity.csv")

    errors = validate_inputs(
        audit_summary,
        ingestion_summary,
        capacity_summary,
        args.audit_dir,
        args.ingestion_dir,
        args.capacity_dir,
    )

    target_summary = ingestion_summary.get("target_summary", {})
    shortcut_counts = audit_summary.get("counts", {})
    key_diagnostics = {
        "audit_status": audit_summary.get("status"),
        "allowed_high_risk_blockers": shortcut_counts.get("allowed_high_risk_blockers"),
        "target_counts": audit_summary.get("target_counts", {}),
        "combined_p_rel_predicate_class_pair_capacity": find_capacity(
            capacity_rows, "p_rel_combined", "predicate_subject_object_class_pair"
        ),
        "hanging_on_subject_class_capacity": find_capacity(
            capacity_rows, "p_rel_hanging_on", "subject_label"
        ),
        "hanging_on_class_pair_capacity": find_capacity(
            capacity_rows, "p_rel_hanging_on", "subject_object_class_pair"
        ),
        "hanging_on_predicate_class_pair_capacity": find_capacity(
            capacity_rows, "p_rel_hanging_on", "predicate_subject_object_class_pair"
        ),
        "pre_label_full_train_proxy_capacity_note": {
            "mixed_groups_available_before_visual_labeling": capacity_summary.get("counts", {}).get("mixed_exact_groups", "see_artifact"),
            "selected_candidate_groups": "160 mixed exact predicate/class-pair groups were selected before packet label fill",
            "post_label_failure": "visible labels collapsed those groups into pure class-prior targets",
        },
    }

    option_rows = [
        {
            "option": "run_learned_smoke_on_combined_p_rel",
            "decision": "reject",
            "reason": "predicate_subject_object_class_pair reaches majority accuracy 1.0",
            "risk": "would test class-pair memorization rather than C_e/Q_e",
        },
        {
            "option": "run_hanging_on_only_learned_smoke",
            "decision": "reject",
            "reason": "hanging_on has 86/90 mass but subject_label and class_pair each reach accuracy 1.0",
            "risk": "balanced labels are not independent labels",
        },
        {
            "option": "mine_again_with_same_proxy_recipe",
            "decision": "reject",
            "reason": "one full-train exact class-pair repair attempt already collapsed after visible labels",
            "risk": "same proxy recipe is likely to reproduce object-class prior",
        },
        {
            "option": "mine_truly_mixed_same_class_pair_visual_rows",
            "decision": "defer",
            "reason": "requires a new audit protocol that selects rows by visible/mesh evidence, not source proxy buckets",
            "risk": "expensive and not justified before scope synthesis",
        },
        {
            "option": "reframe_as_p_obs_abstention_route",
            "decision": "defer",
            "reason": "current packets are T1-ready and p_obs is 455/25 negative-sparse",
            "risk": "requires low-observability/occlusion-focused mining",
        },
        {
            "option": "freeze_r7_class_pair_repair_as_diagnostic",
            "decision": "select",
            "reason": "preserves negative evidence and avoids unsupported learned-compatibility claim",
            "risk": "R7 cannot be used as main learned route yet",
        },
    ]
    route_rows = [
        {
            "route": "R7_attachment_observability_current_artifact",
            "status": "diagnostic_freeze",
            "claim_allowed": "diagnostic_negative_evidence_only",
            "claim_blocked": "learned C_e/Q_e route success, calibrated p_rel/p_obs, paper-level reliability result",
            "next_action": NEXT_TODO,
        },
        {
            "route": "R7_future_revisit_condition",
            "status": "deferred",
            "claim_allowed": "future if new target construction is source/class-prior independent",
            "claim_blocked": "same proxy-based class-pair mining",
            "next_action": "requires visible_evidence_first_sampling_or_low_observability_mining",
        },
        {
            "route": "H002_scope",
            "status": "needs_scope_synthesis",
            "claim_allowed": "relation-aware route taxonomy with R7 diagnostic boundary",
            "claim_blocked": "all-family solved reliability",
            "next_action": NEXT_TODO,
        },
    ]
    risk_rows = [
        {
            "risk": "object_class_prior_target",
            "severity": "high",
            "evidence": "hanging_on subject_label/class_pair accuracy 1.0",
            "action": "freeze current target as diagnostic",
        },
        {
            "risk": "proxy_repair_not_label_repair",
            "severity": "high",
            "evidence": "pre-label mixed proxy groups did not survive visible labels",
            "action": "do not repeat same proxy mining recipe",
        },
        {
            "risk": "p_obs_sparse",
            "severity": "medium",
            "evidence": "p_obs positive/negative 455/25",
            "action": "needs low-observability mining if R7 p_obs is revisited",
        },
        {
            "risk": "claim_overreach",
            "severity": "high",
            "evidence": "no learned model, no independent target, no validation/test",
            "action": "no paper-level claim from R7 current artifact",
        },
    ]
    next_contract = {
        "next_todo": NEXT_TODO,
        "purpose": "Update H002 relation-family route scope after freezing R7 current artifact.",
        "must_include": [
            "R7 current artifact diagnostic-only boundary",
            "R7 future revisit conditions",
            "impact on relation-aware evidence routing claim",
            "whether to probe another family or consolidate current evidence",
        ],
        "must_not_do": [
            "run learned smoke on current R7 class-pair repair target",
            "promote R7 current artifact to paper evidence",
            "reuse same proxy recipe without a new target definition",
        ],
    }

    status = STATUS_ERROR if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_root": rel_path(args.output_dir),
        "status": status,
        "selected_path": "input_errors_stop" if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only_path_decision",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "fills_new_labels": False,
            "materializes_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
        },
        "input_paths": {
            "audit_summary": rel_path(args.audit_dir / "summary.json"),
            "ingestion_summary": rel_path(args.ingestion_dir / "summary.json"),
            "capacity_summary": rel_path(args.capacity_dir / "summary.json"),
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "key_diagnostics": rel_path(args.output_dir / "key_diagnostics.json"),
            "option_decision": rel_path(args.output_dir / "option_decision.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "risk_register": rel_path(args.output_dir / "risk_register.csv"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "decision_summary": {
            "selected": "freeze_r7_class_pair_repair_as_diagnostic",
            "learned_smoke_allowed": False,
            "rejected_learned_targets": [
                "combined_observable_p_rel",
                "hanging_on_observable_p_rel",
                "attached_to_observable_p_rel",
                "p_obs_current_packet_set",
            ],
            "target_summary": target_summary,
            "key_diagnostics": key_diagnostics,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "key_diagnostics.json", key_diagnostics)
    write_json(args.output_dir / "next_contract.json", next_contract)
    write_csv(args.output_dir / "option_decision.csv", option_rows)
    write_csv(args.output_dir / "route_decision.csv", route_rows)
    write_csv(args.output_dir / "risk_register.csv", risk_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
