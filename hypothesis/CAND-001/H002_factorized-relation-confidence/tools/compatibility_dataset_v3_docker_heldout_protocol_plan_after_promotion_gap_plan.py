#!/usr/bin/env python3
"""Plan Docker and grouped-holdout protocol for H002 promotion."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROMOTION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan"
)

PROPOSED_EXPERIMENT_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing"
PROPOSED_CONFIG_ROOT = REPO_ROOT / "configs/h002"
PROPOSED_RESULTS_ROOT = REPO_ROOT / "results/h002_compatibility_routing"

EXPECTED_PROMOTION_STATUS = (
    "h002_compatibility_dataset_v3_promotion_gap_plan_after_paper_framework_readiness_review_ready"
)
EXPECTED_PROMOTION_NEXT = "compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_docker_heldout_protocol_plan_after_promotion_gap_plan_input_errors"
)
SELECTED_PATH = "docker_heldout_protocol_ready_select_experiment_root_skeleton"
NEXT_TODO = "compatibility_dataset_v3_experiment_root_skeleton_after_docker_heldout_protocol_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--promotion-dir", type=Path, default=DEFAULT_PROMOTION_DIR)
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
    if not path.exists():
        return []
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


def validation_count(summary: dict[str, Any]) -> int:
    for key in ("validation_errors", "validation_error_count"):
        if key in summary:
            return int(summary.get(key) or 0)
    return 0


def validate_inputs(
    summary: dict[str, Any],
    roadmap: list[dict[str, str]],
    route_matrix: list[dict[str, str]],
    promotion_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PROMOTION_STATUS:
        errors.append(
            {
                "error_type": "unexpected_promotion_status",
                "expected": EXPECTED_PROMOTION_STATUS,
                "actual": summary.get("status"),
            }
        )
    if summary.get("next_todo") != EXPECTED_PROMOTION_NEXT:
        errors.append(
            {
                "error_type": "unexpected_promotion_next_todo",
                "expected": EXPECTED_PROMOTION_NEXT,
                "actual": summary.get("next_todo"),
            }
        )
    if validation_count(summary) != 0:
        errors.append({"error_type": "promotion_validation_errors", "actual": validation_count(summary)})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "new_model_or_smoke_run", "docker_experiment_created"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "input_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("paper_level_ready") is not False:
        errors.append({"error_type": "promotion_input_already_paper_level_ready"})

    validation_file = promotion_dir / "validation_errors.jsonl"
    if validation_file.exists() and validation_file.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "promotion_validation_error_rows_present"})

    p1 = [row for row in roadmap if row.get("step") == "P1"]
    if len(p1) != 1 or p1[0].get("status") != "next":
        errors.append({"error_type": "p1_not_next", "rows": p1})
    candidate_rows = [row for row in route_matrix if row.get("promotion_role") == "candidate_main_mechanism"]
    if len(candidate_rows) != 4:
        errors.append({"error_type": "unexpected_candidate_route_count", "actual": len(candidate_rows)})
    return errors


def protocol_scope(route_matrix: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in route_matrix:
        promote = row.get("promotion_role") == "candidate_main_mechanism"
        rows.append(
            {
                "family": row.get("family", ""),
                "predicates": row.get("predicates", ""),
                "protocol_role": "promoted_candidate" if promote else "diagnostic_or_deferred",
                "priority": row.get("priority", ""),
                "included_in_docker_reproduction": str(promote),
                "included_in_grouped_holdout_metric": str(promote),
                "included_in_calibration": "only_if_p_rel_p_obs_claim" if promote else "false",
                "claim_boundary": row.get("paper_claim_if_pass", ""),
                "failure_boundary": row.get("paper_claim_if_fail", ""),
            }
        )
    return rows


def proposed_root_plan() -> list[dict[str, Any]]:
    return [
        {
            "path": rel_path(PROPOSED_EXPERIMENT_ROOT),
            "role": "future H002 Docker experiment workspace",
            "create_now": "false",
            "owner_file_required": "README.md",
            "notes": "Create only in the next step after this protocol is accepted.",
        },
        {
            "path": rel_path(PROPOSED_EXPERIMENT_ROOT / "commands.md"),
            "role": "future concise command index",
            "create_now": "false",
            "owner_file_required": "commands.md",
            "notes": "Must record Docker commands, expected outputs, and validation commands.",
        },
        {
            "path": rel_path(PROPOSED_CONFIG_ROOT),
            "role": "future Dockerfile/compose root for H002",
            "create_now": "false",
            "owner_file_required": "README.md or compose comments",
            "notes": "Must be linked from configs/README.md if created.",
        },
        {
            "path": rel_path(PROPOSED_RESULTS_ROOT),
            "role": "future compact paper-facing H002 summaries",
            "create_now": "false",
            "owner_file_required": "README.md if durable",
            "notes": "Only compact manifests/tables go here; row-level outputs stay under experiments/ or ignored runtime roots.",
        },
    ]


def mount_plan() -> list[dict[str, Any]]:
    return [
        {
            "mount_name": "repo",
            "host_path": rel_path(REPO_ROOT),
            "container_path": "/workspace/research",
            "mode": "rw",
            "reason": "Execute tracked code and write compact tracked protocol/result artifacts.",
        },
        {
            "mount_name": "local_dataset",
            "host_path": "local_dataset/",
            "container_path": "/data/local_dataset",
            "mode": "ro",
            "reason": "Read 3DSSG/3RScan/Open3DSG-staged data without tracking large payloads.",
        },
        {
            "mount_name": "h002_hypothesis_artifacts",
            "host_path": rel_path(H2_ROOT / "artifacts"),
            "container_path": "/workspace/research/hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts",
            "mode": "ro_for_inputs_rw_for_new_outputs",
            "reason": "Read prior hypothesis artifacts and write new promoted-route manifests only under explicit output roots.",
        },
        {
            "mount_name": "h001_reference_artifacts_optional",
            "host_path": "results/h001_geom_reliability/ and archive/experiments/H001_geom_reliability/",
            "container_path": "/workspace/research/<same-relative-path>",
            "mode": "ro",
            "reason": "Reference source outputs only via explicit manifests; never modify H001 artifacts.",
        },
        {
            "mount_name": "logs",
            "host_path": "logs/",
            "container_path": "/workspace/research/logs",
            "mode": "rw",
            "reason": "Record long-running command logs and validation logs.",
        },
    ]


def compose_service_plan() -> list[dict[str, Any]]:
    return [
        {
            "service": "h002-protocol-check",
            "stage": "preflight",
            "command_purpose": "Verify mounted paths, previous artifact statuses, and proposed output roots.",
            "paper_metric": "false",
            "required_output": "mount_check.json; validation_errors.jsonl",
        },
        {
            "service": "h002-materialize-routes",
            "stage": "P2",
            "command_purpose": "Regenerate promoted candidate route rows and model-safe/hidden manifests in Docker.",
            "paper_metric": "false_until_metric_gate",
            "required_output": "route_rows.jsonl; model_safe_view.jsonl; hidden_manifest.jsonl; row_manifest.json",
        },
        {
            "service": "h002-shortcut-audit",
            "stage": "P5",
            "command_purpose": "Run schema leakage, class-pair/source/rank/endpoint, wrong-T, and shuffled-G audits.",
            "paper_metric": "false",
            "required_output": "shortcut_audit.csv; control_metrics.csv; validation_errors.jsonl",
        },
        {
            "service": "h002-grouped-eval",
            "stage": "P3",
            "command_purpose": "Run grouped holdout route metrics and controls for candidate routes.",
            "paper_metric": "eligible_after_pass",
            "required_output": "route_metrics.csv; control_metrics.csv; split_manifest.json",
        },
        {
            "service": "h002-calibration",
            "stage": "P4_optional",
            "command_purpose": "Run calibration/selective-risk only if p_rel/p_obs claims remain active.",
            "paper_metric": "eligible_only_for_calibration_claim_after_pass",
            "required_output": "calibration_metrics.csv; reliability_diagram_data.csv; selective_risk.csv",
        },
    ]


def heldout_split_policy() -> list[dict[str, Any]]:
    return [
        {
            "policy": "source_pool",
            "value": "H002 candidate source pool; do not call this official validation/test unless official splits are explicitly used later.",
            "pass_check": "summary must state source_pool and official_validation_usage=false.",
        },
        {
            "policy": "primary_group",
            "value": "scan_id",
            "pass_check": "0 scan_id overlap across train/dev/heldout groups.",
        },
        {
            "policy": "secondary_group_guard",
            "value": "endpoint_pair_id or scan_id:subject_id:object_id when available",
            "pass_check": "0 endpoint-pair overlap across train/dev/heldout groups.",
        },
        {
            "policy": "split_ratio",
            "value": "train/dev/heldout = 70/15/15 by groups, adjustable only before metrics if a route becomes single-class",
            "pass_check": "all promoted routes retain both positive and negative rows in dev and heldout.",
        },
        {
            "policy": "stratification",
            "value": "route family, predicate label, target label, and scan count mass",
            "pass_check": "per-family split count table exists; any route with single-class heldout is demoted from paper metric.",
        },
        {
            "policy": "tuning_boundary",
            "value": "Use train/dev for model/threshold selection; heldout is read once for final reported route metrics.",
            "pass_check": "final report records selected hyperparameters before heldout scoring.",
        },
    ]


def output_manifest_contract() -> list[dict[str, Any]]:
    return [
        {
            "file": "run_manifest.json",
            "required_fields": "schema_version,status,created_at,command,git_commit,input_roots,output_roots,validation_errors",
            "owner": "each Docker run",
        },
        {
            "file": "split_manifest.json",
            "required_fields": "split_policy,group_keys,counts_by_split,counts_by_route,group_overlap_audit",
            "owner": "grouped split stage",
        },
        {
            "file": "route_rows.jsonl",
            "required_fields": "route_id,family,predicate,scan_id,subject_id,object_id,target,split,model_safe_id",
            "owner": "materialization stage",
        },
        {
            "file": "model_safe_view.jsonl",
            "required_fields": "model_safe_id,T_e_fields,G_e_fields,Q_e_fields,optional_Z_e_fields,split",
            "owner": "materialization stage",
        },
        {
            "file": "hidden_manifest.jsonl",
            "required_fields": "model_safe_id,construction_fields,source/proxy fields,blocked fields,diagnostic provenance",
            "owner": "materialization stage; never model input",
        },
        {
            "file": "route_metrics.csv",
            "required_fields": "family,predicate,split,model_view,metric,value,n_pos,n_neg,n_abstain",
            "owner": "grouped evaluation stage",
        },
        {
            "file": "control_metrics.csv",
            "required_fields": "family,split,control_type,metric,value,pass_fail",
            "owner": "shortcut/control stage",
        },
        {
            "file": "validation_errors.jsonl",
            "required_fields": "error_type,path_or_row_id,details",
            "owner": "all stages",
        },
    ]


def route_metric_contract() -> list[dict[str, Any]]:
    common_controls = "T_only,G_only,plain_concat,wrong_T,shuffled_G_global,shuffled_G_within_family,class_pair_probe,source_rank_probe"
    return [
        {
            "family": "relative_vertical",
            "predicates": "higher than; lower than",
            "primary_metric": "AUROC/AUPRC/balanced_accuracy for C_e",
            "minimum_gate": "heldout AUROC >= 0.90 and controls collapse",
            "controls": common_controls,
            "claim_if_pass": "clean vertical predicate-geometry compatibility route",
        },
        {
            "family": "size_relative",
            "predicates": "bigger than; smaller than",
            "primary_metric": "AUROC/AUPRC/balanced_accuracy for C_e",
            "minimum_gate": "heldout AUROC >= 0.90 and controls collapse",
            "controls": common_controls,
            "claim_if_pass": "clean size predicate-geometry compatibility route",
        },
        {
            "family": "relative_horizontal",
            "predicates": "left; right; front; behind",
            "primary_metric": "AUROC/AUPRC/balanced_accuracy for C_e under frozen frame convention",
            "minimum_gate": "heldout AUROC >= 0.85, explicit frame caveat, controls collapse",
            "controls": common_controls + ",wrong_frame_or_axis_when_available",
            "claim_if_pass": "frame-aware horizontal compatibility route, excluding complete horizontal ontology claims",
        },
        {
            "family": "support_contact",
            "predicates": "standing on; lying on",
            "primary_metric": "AUROC/AUPRC/balanced_accuracy for C_e; failure slices by predicate and Q_e",
            "minimum_gate": "heldout AUROC >= 0.65 and >= 0.10 above best T/G/concat baseline; wrong-T below primary by >= 0.10; shuffled-G near chance",
            "controls": common_controls + ",Q_shuffle,predicate_slice,limited_vs_sufficient_Q_e_slice",
            "claim_if_pass": "challenging support/contact route needs predicate-contact compatibility, not fully solved relation reliability",
        },
    ]


def control_matrix() -> list[dict[str, Any]]:
    return [
        {
            "control": "T_only",
            "purpose": "semantic content without geometry",
            "must_report_for": "all promoted routes",
            "pass_logic": "primary C_e should outperform it unless route is intentionally semantic-only, which current promoted routes are not",
        },
        {
            "control": "G_only",
            "purpose": "predicate-independent geometry without predicate text",
            "must_report_for": "all promoted routes",
            "pass_logic": "G_only must not solve predicate-flip compatibility routes; proximity remains separate diagnostic",
        },
        {
            "control": "plain_concat",
            "purpose": "fixed fusion baseline without explicit compatibility interaction",
            "must_report_for": "all promoted routes",
            "pass_logic": "C_e should outperform or at least provide control-collapse evidence beyond concat",
        },
        {
            "control": "wrong_T",
            "purpose": "same geometry with wrong predicate semantics",
            "must_report_for": "all promoted routes",
            "pass_logic": "score should collapse when predicate semantics are wrong",
        },
        {
            "control": "shuffled_G",
            "purpose": "same predicate with mismatched geometry",
            "must_report_for": "all promoted routes",
            "pass_logic": "score should collapse or move near chance when geometry is shuffled",
        },
        {
            "control": "class_pair_probe",
            "purpose": "detect object-class shortcut",
            "must_report_for": "all promoted routes",
            "pass_logic": "allowed model-safe class fields must not solve the target by themselves",
        },
        {
            "control": "source_rank_probe",
            "purpose": "detect source confidence/rank shortcut",
            "must_report_for": "all promoted routes",
            "pass_logic": "Z_e cannot enter C_e; any Z_e use in final reliability must be ablated",
        },
        {
            "control": "endpoint_pair_leakage",
            "purpose": "detect same-pair memorization across splits",
            "must_report_for": "all promoted routes",
            "pass_logic": "0 endpoint-pair overlap across reported splits",
        },
    ]


def leakage_audit_plan() -> list[dict[str, Any]]:
    return [
        {
            "audit": "blocked_field_schema_scan",
            "input": "model_safe_view.jsonl",
            "output": "schema_leakage_report.json",
            "pass_gate": "0 blocked field names and 0 hidden construction fields",
        },
        {
            "audit": "group_overlap_audit",
            "input": "split_manifest.json",
            "output": "group_overlap_report.json",
            "pass_gate": "0 scan overlap and 0 endpoint-pair overlap",
        },
        {
            "audit": "single_feature_probe",
            "input": "model_safe_view.jsonl + targets",
            "output": "single_feature_probe.csv",
            "pass_gate": "no allowed single feature reaches route-specific shortcut threshold",
        },
        {
            "audit": "hidden_manifest_join_check",
            "input": "hidden_manifest.jsonl",
            "output": "hidden_manifest_audit.json",
            "pass_gate": "hidden fields are used only after prediction for diagnostics",
        },
        {
            "audit": "counterfactual_integrity",
            "input": "wrong-T and shuffled-G manifests",
            "output": "counterfactual_integrity.csv",
            "pass_gate": "counterfactual ids are split-consistent and do not leak construction labels",
        },
    ]


def pass_fail_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "D0",
            "stage": "protocol",
            "pass_condition": "This artifact has validation_errors=0 and no experiment root was created.",
            "fail_action": "Fix protocol before creating any H002 experiment root.",
        },
        {
            "gate_id": "D1",
            "stage": "docker_preflight",
            "pass_condition": "all required mounts resolve; prior artifact statuses match; H001 inputs are read-only",
            "fail_action": "do not materialize promoted rows",
        },
        {
            "gate_id": "D2",
            "stage": "materialization",
            "pass_condition": "promoted route rows exist, both labels present per split, validation_errors=0",
            "fail_action": "demote affected route or repair target before metrics",
        },
        {
            "gate_id": "D3",
            "stage": "grouped_holdout",
            "pass_condition": "0 group leakage; route metrics meet family-specific thresholds; controls collapse",
            "fail_action": "report as diagnostic, not paper-level route result",
        },
        {
            "gate_id": "D4",
            "stage": "calibration_optional",
            "pass_condition": "ECE/Brier/NLL/selective-risk improve or are defensible against uncalibrated score",
            "fail_action": "keep C_e mechanism claim only; block calibrated p_rel/p_obs",
        },
        {
            "gate_id": "D5",
            "stage": "claim_lock",
            "pass_condition": "paper wording matches passed gates and blocked claims remain explicit",
            "fail_action": "do not draft main table/prose from H002",
        },
    ]


def blocked_actions() -> list[dict[str, Any]]:
    return [
        {
            "action": "create experiments/H002_compatibility_routing in this step",
            "status": "blocked_now",
            "reason": "This TODO is a protocol plan only.",
        },
        {
            "action": "run paper-level H002 metrics from host scripts",
            "status": "blocked",
            "reason": "Paper-facing experiments must be Docker-based.",
        },
        {
            "action": "use official validation/test language for current train-source holdout",
            "status": "blocked",
            "reason": "Current plan defines grouped holdout inside the H002 candidate source pool unless official splits are explicitly adopted later.",
        },
        {
            "action": "promote R7 attachment-like learned reliability",
            "status": "blocked",
            "reason": "Current R7 target is shortcut-prone and diagnostic-only.",
        },
        {
            "action": "claim calibrated p_rel/p_obs from C_e AUROC",
            "status": "blocked",
            "reason": "Calibration/selective-decision metrics are required.",
        },
    ]


def command_contract() -> list[dict[str, Any]]:
    return [
        {
            "command_name": "preflight",
            "future_command_shape": "docker compose -f configs/h002/compose.yaml run --rm h002-protocol-check",
            "runs_now": "false",
            "expected_exit": "0",
            "expected_outputs": "mount_check.json; validation_errors.jsonl",
        },
        {
            "command_name": "materialize",
            "future_command_shape": "docker compose -f configs/h002/compose.yaml run --rm h002-materialize-routes",
            "runs_now": "false",
            "expected_exit": "0",
            "expected_outputs": "route_rows.jsonl; model_safe_view.jsonl; hidden_manifest.jsonl",
        },
        {
            "command_name": "audit",
            "future_command_shape": "docker compose -f configs/h002/compose.yaml run --rm h002-shortcut-audit",
            "runs_now": "false",
            "expected_exit": "0",
            "expected_outputs": "shortcut_audit.csv; control_metrics.csv",
        },
        {
            "command_name": "grouped_eval",
            "future_command_shape": "docker compose -f configs/h002/compose.yaml run --rm h002-grouped-eval",
            "runs_now": "false",
            "expected_exit": "0",
            "expected_outputs": "route_metrics.csv; split_manifest.json; control_metrics.csv",
        },
        {
            "command_name": "calibration_optional",
            "future_command_shape": "docker compose -f configs/h002/compose.yaml run --rm h002-calibration",
            "runs_now": "false",
            "expected_exit": "0 if calibration claim is pursued",
            "expected_outputs": "calibration_metrics.csv; selective_risk.csv",
        },
    ]


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Docker Heldout Protocol Plan",
        "",
        "## Verdict",
        "",
        (
            "The protocol is ready for a future experiment-root skeleton. No H002 Docker root was "
            "created in this step, no model was run, and no paper-level metric was produced."
        ),
        "",
        "## Proposed Roots",
        "",
        "| Path | Role | Create now |",
        "| --- | --- | --- |",
    ]
    for row in payload["proposed_root_plan"]:
        lines.append("| {path} | {role} | {create_now} |".format(**row))
    lines.extend(
        [
            "",
            "## Promoted Candidate Routes",
            "",
            "| Family | Predicates | Included in grouped metric |",
            "| --- | --- | --- |",
        ]
    )
    for row in payload["protocol_scope"]:
        if row["protocol_role"] == "promoted_candidate":
            lines.append(
                "| {family} | {predicates} | {included_in_grouped_holdout_metric} |".format(**row)
            )
    lines.extend(
        [
            "",
            "## Split Policy",
            "",
            "| Policy | Value |",
            "| --- | --- |",
        ]
    )
    for row in payload["heldout_split_policy"]:
        lines.append("| {policy} | {value} |".format(**row))
    lines.extend(
        [
            "",
            "## Pass/Fail Gates",
            "",
            "| Gate | Stage | Pass condition |",
            "| --- | --- | --- |",
        ]
    )
    for row in payload["pass_fail_gates"]:
        lines.append("| {gate_id} | {stage} | {pass_condition} |".format(**row))
    lines.extend(["", "## Next", "", f"`{NEXT_TODO}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary = read_json(args.promotion_dir / "summary.json")
    roadmap = read_csv(args.promotion_dir / "promotion_roadmap.csv")
    route_matrix_input = read_csv(args.promotion_dir / "route_gate_matrix.csv")
    errors = validate_inputs(summary, roadmap, route_matrix_input, args.promotion_dir)

    scope = protocol_scope(route_matrix_input)
    root_plan = proposed_root_plan()
    mounts = mount_plan()
    services = compose_service_plan()
    split_policy = heldout_split_policy()
    output_manifest = output_manifest_contract()
    metrics = route_metric_contract()
    controls = control_matrix()
    leakage = leakage_audit_plan()
    gates = pass_fail_gates()
    blocked = blocked_actions()
    commands = command_contract()

    if PROPOSED_EXPERIMENT_ROOT.exists():
        # Do not fail: this could be user-created state, but record it explicitly.
        root_exists_note = "true"
    else:
        root_exists_note = "false"

    if not any(row["mount_name"] == "h001_reference_artifacts_optional" for row in mounts):
        errors.append({"error_type": "missing_h001_readonly_mount_plan"})
    if not any(row["policy"] == "source_pool" for row in split_policy):
        errors.append({"error_type": "missing_source_pool_policy"})
    if not any(row["gate_id"] == "D0" for row in gates):
        errors.append({"error_type": "missing_protocol_no_root_gate"})

    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_input_errors_before_docker_heldout_protocol",
        "next_todo": NEXT_TODO if not errors else EXPECTED_PROMOTION_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "official_validation_usage": False,
            "new_model_or_smoke_run": False,
            "docker_experiment_created": False,
            "proposed_experiment_root_exists_at_plan_time": root_exists_note,
            "h001_artifacts_modified": False,
            "paper_level_ready": False,
            "framework_ready_hypothesis_stage": not errors,
        },
        "input_artifacts": {"promotion_gap_plan": rel_path(args.promotion_dir)},
        "decision_summary": {
            "protocol_status": "ready_for_future_experiment_root_skeleton" if not errors else "blocked",
            "proposed_experiment_root": rel_path(PROPOSED_EXPERIMENT_ROOT),
            "proposed_config_root": rel_path(PROPOSED_CONFIG_ROOT),
            "proposed_results_root": rel_path(PROPOSED_RESULTS_ROOT),
            "source_pool_boundary": "grouped holdout inside H002 candidate source pool; not official validation/test",
            "promoted_candidate_routes": [
                "relative_vertical",
                "size_relative",
                "relative_horizontal",
                "support_contact",
            ],
            "paper_metrics_produced": False,
        },
        "protocol_scope": scope,
        "proposed_root_plan": root_plan,
        "docker_mount_plan": mounts,
        "compose_service_plan": services,
        "heldout_split_policy": split_policy,
        "output_manifest_contract": output_manifest,
        "route_metric_contract": metrics,
        "control_matrix": controls,
        "leakage_audit_plan": leakage,
        "pass_fail_gates": gates,
        "blocked_actions": blocked,
        "command_contract": commands,
    }

    write_csv(args.output_dir / "protocol_scope.csv", scope)
    write_csv(args.output_dir / "proposed_root_plan.csv", root_plan)
    write_csv(args.output_dir / "docker_mount_plan.csv", mounts)
    write_csv(args.output_dir / "compose_service_plan.csv", services)
    write_csv(args.output_dir / "heldout_split_policy.csv", split_policy)
    write_csv(args.output_dir / "output_manifest_contract.csv", output_manifest)
    write_csv(args.output_dir / "route_metric_contract.csv", metrics)
    write_csv(args.output_dir / "control_matrix.csv", controls)
    write_csv(args.output_dir / "leakage_audit_plan.csv", leakage)
    write_csv(args.output_dir / "pass_fail_gates.csv", gates)
    write_csv(args.output_dir / "blocked_actions.csv", blocked)
    write_csv(args.output_dir / "command_contract.csv", commands)
    write_json(
        args.output_dir / "next_contract.json",
        {
            "next_todo": NEXT_TODO,
            "must_do": [
                "create minimal experiment/config/results skeleton only if proceeding with H002 promotion",
                "update experiments/README.md, configs/README.md, docs/index.md, and root TODO if a durable root is created",
                "keep H001 artifacts read-only and record all Docker commands before metrics",
            ],
            "must_not_do": [
                "run paper-level H002 metrics before Docker preflight and split manifest exist",
                "call grouped holdout official validation/test",
                "promote p_rel/p_obs calibration without calibration metrics",
            ],
        },
    )
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
