#!/usr/bin/env python3
"""Choose the next independent target-source route after H002 scope synthesis."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCOPE_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze"
)
DEFAULT_TRAIN_RGA_SUMMARY = (
    H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga/train_rga_summary.json"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis"
)

EXPECTED_SCOPE_STATUS = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_freeze_ready"
EXPECTED_SCOPE_NEXT = "compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_target_source_decision_selected"
STATUS_ERROR = "h002_compatibility_dataset_v3_independent_target_source_decision_input_errors"
SELECTED_PATH = "select_support_contact_visual_mesh_human_audit_with_size_containment_probe"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--train-rga-summary", type=Path, default=DEFAULT_TRAIN_RGA_SUMMARY)
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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_required(path: Path, errors: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not path.exists():
        errors.append({"input": label, "error_type": "missing_file", "path": rel_path(path)})
        return {}
    return read_json(path)


def validate_inputs(scope_summary: dict[str, Any], train_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if scope_summary.get("status") != EXPECTED_SCOPE_STATUS:
        errors.append(
            {
                "input": "scope_summary",
                "error_type": "unexpected_status",
                "actual": scope_summary.get("status"),
                "expected": EXPECTED_SCOPE_STATUS,
            }
        )
    if scope_summary.get("next_todo") != EXPECTED_SCOPE_NEXT:
        errors.append(
            {
                "input": "scope_summary",
                "error_type": "unexpected_next_todo",
                "actual": scope_summary.get("next_todo"),
                "expected": EXPECTED_SCOPE_NEXT,
            }
        )
    if scope_summary.get("validation_errors") != 0:
        errors.append(
            {
                "input": "scope_summary",
                "error_type": "validation_errors_present",
                "actual": scope_summary.get("validation_errors"),
            }
        )
    boundary = scope_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke"]:
        if boundary.get(key) is not False:
            errors.append({"input": "scope_summary", "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    train_boundary = train_summary.get("boundary", {})
    if train_boundary.get("split") != "train full only":
        errors.append({"input": "train_rga_summary", "error_type": "unexpected_split", "actual": train_boundary.get("split")})
    if train_boundary.get("not_paper_result") is not True:
        errors.append(
            {
                "input": "train_rga_summary",
                "error_type": "unexpected_paper_boundary",
                "actual": train_boundary.get("not_paper_result"),
            }
        )
    return errors


def count_labels(summary: dict[str, Any], labels: list[str]) -> tuple[int, str]:
    predicate_counts = summary.get("ground_truth", {}).get("predicate_label", {})
    counts = {label: int(predicate_counts.get(label, 0)) for label in labels}
    return sum(counts.values()), "; ".join(f"{label}: {counts[label]}" for label in labels)


def route_rows(scope_summary: dict[str, Any], train_summary: dict[str, Any]) -> list[dict[str, Any]]:
    cb = scope_summary.get("claim_boundary", {})
    primary = cb.get("primary_evidence", {})
    support = cb.get("support_contact_boundary", {})
    gt_family = train_summary.get("ground_truth", {}).get("predicate_family", {})
    return [
        {
            "route": "relative_vertical_heldout_docker_promotion",
            "verdict": "defer_not_main",
            "priority": 3,
            "reason": (
                "It is the cleanest current C_e evidence, but it would make H002 a narrow higher/lower "
                "compatibility paper rather than solve the broader target-source blocker."
            ),
            "supporting_evidence": (
                f"primary AUROC {primary.get('primary_auroc')}; geometry-only {primary.get('geometry_only_auroc')}; "
                f"source-only {primary.get('source_only_auroc')}"
            ),
            "next_action": "keep as internal anchor and possible later Docker promotion if no stronger source is found",
        },
        {
            "route": "support_contact_human_visual_mesh_audit_target",
            "verdict": "selected_main",
            "priority": 1,
            "reason": (
                "This route directly addresses the current blocker: support/contact has enough raw family mass and "
                "mesh/pose/contact evidence, but Open3DSG train-side independent-validity targets collapse under "
                "predicate/class shortcuts."
            ),
            "supporting_evidence": (
                f"support/contact GT family {gt_family.get('support_contact')}; strict predicate-class capacity "
                f"{support.get('strict_predicate_class_capacity')}; pose-conditioned C_e already works but independent "
                "validity remains diagnostic-only"
            ),
            "next_action": NEXT_TODO,
        },
        {
            "route": "cross_source_agreement_target",
            "verdict": "defer_secondary",
            "priority": 4,
            "reason": (
                "Cross-source agreement can reduce single-source shortcut risk, but source disagreement is not "
                "automatically reliability GT and can encode source-specific bias."
            ),
            "supporting_evidence": "No frozen cross-source H002 target source is available in the current artifact contract.",
            "next_action": "revisit after support/contact audit schema or if a second source target can be locked",
        },
        {
            "route": "stop_h002_as_mechanism_evidence",
            "verdict": "reject_for_now",
            "priority": 5,
            "reason": (
                "Stopping is defensible for the H001/GeoCalib paper timeline, but the selected support/contact audit "
                "route is still the most direct way to test whether H002 can become an independent method."
            ),
            "supporting_evidence": "Current H002 is not paper-ready, but the blocker is identifiable.",
            "next_action": "keep as fallback if the next audit target cannot satisfy independence gates",
        },
        {
            "route": "relation_type_expansion_only",
            "verdict": "reject_as_main_select_optional_probe",
            "priority": 2,
            "reason": (
                "Adding relation types without a better target source repeats the same shortcut problem. A small "
                "size/containment feasibility probe is useful only as generality evidence."
            ),
            "supporting_evidence": "size and containment labels exist, but most are unsupported by the current first-pass geometry policy.",
            "next_action": "run only after or alongside the selected support/contact audit plan as a bounded feasibility scan",
        },
    ]


def optional_probe_rows(train_summary: dict[str, Any]) -> list[dict[str, Any]]:
    size_total, size_counts = count_labels(train_summary, ["bigger than", "smaller than"])
    containment_labels = ["standing in", "lying in", "build in", "part of", "belonging to", "cover", "hanging in"]
    containment_total, containment_counts = count_labels(train_summary, containment_labels)
    leaning_total, leaning_counts = count_labels(train_summary, ["leaning against"])
    identity_total, identity_counts = count_labels(train_summary, ["same as", "same symmetry as"])
    horizontal_total, horizontal_counts = count_labels(train_summary, ["left", "right", "front", "behind"])
    return [
        {
            "probe": "size_relative",
            "predicates": "bigger than; smaller than",
            "gt_total": size_total,
            "gt_counts": size_counts,
            "priority": 1,
            "expected_value": "quick generality check beyond vertical order using OBB volume/extent G_e",
            "main_risk": "too easy and close to existing relative_vertical; novelty weak if used as main",
            "recommended_role": "optional_feasibility_probe",
        },
        {
            "probe": "containment_inclusion",
            "predicates": "; ".join(containment_labels),
            "gt_total": containment_total,
            "gt_counts": containment_counts,
            "priority": 2,
            "expected_value": "high-value test of in/on/part-of compatibility and Q_e abstention",
            "main_risk": "sparse labels and object/container-class shortcut",
            "recommended_role": "optional_high_risk_probe",
        },
        {
            "probe": "leaning_contact_orientation",
            "predicates": "leaning against",
            "gt_total": leaning_total,
            "gt_counts": leaning_counts,
            "priority": 3,
            "expected_value": "physical relation requiring contact plus orientation, aligned with H002",
            "main_risk": "low GT mass and needs normals/orientation evidence",
            "recommended_role": "future_probe_after_mesh_pose_schema",
        },
        {
            "probe": "relative_horizontal",
            "predicates": "left; right; front; behind",
            "gt_total": horizontal_total,
            "gt_counts": horizontal_counts,
            "priority": 4,
            "expected_value": "large row mass and clear semantic family",
            "main_risk": "reference-frame ambiguity; not a target-source fix",
            "recommended_role": "defer_until_frame_contract",
        },
        {
            "probe": "identity_symmetry",
            "predicates": "same as; same symmetry as",
            "gt_total": identity_total,
            "gt_counts": identity_counts,
            "priority": 5,
            "expected_value": "could test shape/identity consistency",
            "main_risk": "mostly identity/shape matching, not semantic-geometry relation compatibility",
            "recommended_role": "not_recommended_for_H002_main",
        },
    ]


def target_contract(scope_summary: dict[str, Any], train_summary: dict[str, Any]) -> dict[str, Any]:
    family_counts = train_summary.get("ground_truth", {}).get("predicate_family", {})
    predicate_counts = train_summary.get("ground_truth", {}).get("predicate_label", {})
    return {
        "selected_main_route": "support_contact_human_visual_mesh_audit_target",
        "selected_predicates": ["lying on", "standing on", "supported by"],
        "primary_target_axes": [
            "C_e predicate-geometry compatibility",
            "Q_e observability/evidence quality",
            "p_obs selective decision",
            "p_rel relation reliability given observable evidence",
        ],
        "required_evidence": [
            "mesh/point contact support",
            "subject/object pose and orientation evidence",
            "surface gap and overlap evidence",
            "multi-view or reviewer-visible confirmation evidence",
            "coverage and uncertainty fields separated from relation truth labels",
        ],
        "label_policy": {
            "accept": "visual/mesh evidence supports the predicate-specific relation, not just a generic nearby/support relation",
            "reject": "evidence contradicts the predicate or supports a different predicate within the same family",
            "abstain": "insufficient coverage, ambiguous pose, occluded contact region, or ontology ambiguity",
        },
        "minimum_gates_before_smoke": [
            "accept/reject class mass passes per primary predicate or controlled pair family",
            "predicate, subject class, object class, predicate_x_class_pair shortcut probes are below threshold",
            "hidden construction fields are excluded from model-safe view",
            "visual/mesh labels are locked before hidden/source metadata join",
            "same-scene or same-class hard negatives accompany positive anchors",
            "Q_e/abstain is separated from p_rel accept/reject",
        ],
        "support_contact_gt_snapshot": {
            "family_gt": family_counts.get("support_contact"),
            "lying_on": predicate_counts.get("lying on"),
            "standing_on": predicate_counts.get("standing on"),
            "supported_by": predicate_counts.get("supported by"),
        },
        "blocked_actions": [
            "do not run another support/contact learned smoke from the frozen Open3DSG train-side independent-validity target",
            "do not promote relative_vertical-only results to broad H002 reliability",
            "do not add a larger combiner before target-source independence gates",
            "do not treat no-GT as negative without audit evidence",
            "do not use validation/test rows for hypothesis target construction",
        ],
        "optional_relation_probe": "size_relative first, containment_inclusion second; both diagnostic unless target independence passes",
    }


def reviewer_risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "audit_labels_seen_as_subjective",
            "severity": "high",
            "current_answer": "Use explicit visual/mesh evidence fields, locked label protocol, and post-lock hidden/source join.",
            "required_next": "Write audit target plan with visible packet schema and label boundary.",
        },
        {
            "risk": "object_class_shortcut_repeats",
            "severity": "high",
            "current_answer": "The next target must be balanced within subject/object class or must report why it is diagnostic-only.",
            "required_next": "Predeclare shortcut probes and pass/fail gates before materialization.",
        },
        {
            "risk": "support_contact_same_as_existing_pose_conditioned_proxy",
            "severity": "medium",
            "current_answer": "The selected route is not another constructed same-G predicate flip; it is an audit target for independent validity.",
            "required_next": "Keep pose-conditioned C_e as mechanism evidence and separate it from p_rel target labels.",
        },
        {
            "risk": "relation_expansion_dilutes_claim",
            "severity": "medium",
            "current_answer": "Size/containment are optional probes, not the main route.",
            "required_next": "Do not run broad expansion until support/contact target-source decision is complete.",
        },
        {
            "risk": "validation_or_test_contamination",
            "severity": "high",
            "current_answer": "Current decision remains train-only and no rows are materialized.",
            "required_next": "Keep all target construction in train-only artifacts until Docker promotion is explicitly selected.",
        },
    ]


def audit_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "field": "review_relation_reliability",
            "values": "accept_reliable; reject_unreliable; abstain_uncertain",
            "role": "human/visual/mesh reliability label",
            "model_input_allowed": "no",
        },
        {
            "field": "review_geometry_support",
            "values": "supported; contradicted; uncertain",
            "role": "evidence axis label for C_e/p_rel analysis",
            "model_input_allowed": "no for label-derived target; yes only if replaced by deployable features",
        },
        {
            "field": "review_observability",
            "values": "sufficient; limited; not_evaluable",
            "role": "Q_e / p_obs target source",
            "model_input_allowed": "no for label; deployable coverage features allowed separately",
        },
        {
            "field": "review_counter_relation",
            "values": "lying_on; standing_on; supported_by; other; none; unknown",
            "role": "records whether another predicate is better supported",
            "model_input_allowed": "no",
        },
        {
            "field": "visible_packet_features",
            "values": "mesh crop; point crop; multiview crops; contact/pose summary",
            "role": "review evidence shown before hidden/source join",
            "model_input_allowed": "audit only at first; deployable subset must be frozen later",
        },
        {
            "field": "hidden_source_metadata",
            "values": "source score; rank; predicate; class pair; scan id; construction role",
            "role": "post-lock shortcut audit only",
            "model_input_allowed": "only Z_e fields after explicit model view contract; construction fields never",
        },
    ]


def report_text(
    *,
    summary: dict[str, Any],
    routes: list[dict[str, Any]],
    probes: list[dict[str, Any]],
    contract: dict[str, Any],
    risks: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append("# H002 Independent Target-Source Decision After Scope Synthesis")
    lines.append("")
    lines.append("Default artifact:")
    lines.append("")
    lines.append("```text")
    lines.append("artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis/")
    lines.append("```")
    lines.append("")
    lines.append("Status:")
    lines.append("")
    lines.append("```text")
    lines.append(f"status = {summary['status']}")
    lines.append(f"selected_path = {summary['selected_path']}")
    lines.append(f"validation_errors = {summary['validation_errors']}")
    lines.append(f"next_todo = {summary['next_todo']}")
    lines.append("```")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("Selected main route:")
    lines.append("")
    lines.append("```text")
    lines.append(summary["decision"]["selected_main_route"])
    lines.append("```")
    lines.append("")
    lines.append(
        "현재 H002의 병목은 relation type 수가 아니라 target source다. 따라서 다음 단계는 "
        "`relative_vertical` 결과를 바로 paper-level로 올리는 것이 아니라, `support_contact`에 대해 "
        "human/visual/mesh audit 기반의 independent target source를 설계하는 것이다."
    )
    lines.append("")
    lines.append("## Route Table")
    lines.append("")
    lines.append("| Route | Verdict | Priority | Reason |")
    lines.append("| --- | --- | ---: | --- |")
    for row in routes:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['priority']} | {row['reason']} |")
    lines.append("")
    lines.append("## Selected Contract")
    lines.append("")
    lines.append("Selected predicates:")
    lines.append("")
    lines.append("```text")
    lines.append(", ".join(contract["selected_predicates"]))
    lines.append("```")
    lines.append("")
    lines.append("Primary target axes:")
    lines.append("")
    for item in contract["primary_target_axes"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Minimum gates before learned smoke:")
    lines.append("")
    for item in contract["minimum_gates_before_smoke"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("Blocked actions:")
    lines.append("")
    for item in contract["blocked_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Optional Relation-Type Probes")
    lines.append("")
    lines.append("| Probe | Predicates | GT Total | Recommended role | Main risk |")
    lines.append("| --- | --- | ---: | --- | --- |")
    for row in probes:
        lines.append(
            f"| `{row['probe']}` | {row['predicates']} | {row['gt_total']} | "
            f"`{row['recommended_role']}` | {row['main_risk']} |"
        )
    lines.append("")
    lines.append("Interpretation:")
    lines.append("")
    lines.append(
        "`bigger than` / `smaller than`은 빠른 generality probe로 가장 현실적이지만, "
        "`higher/lower`와 유사해 main novelty는 약하다. Containment/inclusion 계열은 더 흥미롭지만 "
        "GT가 적고 class shortcut 위험이 크므로 high-risk probe로 둔다."
    )
    lines.append("")
    lines.append("## Reviewer Risks")
    lines.append("")
    lines.append("| Risk | Severity | Current answer | Required next |")
    lines.append("| --- | --- | --- | --- |")
    for row in risks:
        lines.append(f"| `{row['risk']}` | `{row['severity']}` | {row['current_answer']} | {row['required_next']} |")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("- Train-only decision artifact.")
    lines.append("- No validation/test usage.")
    lines.append("- No row materialization.")
    lines.append("- No learned smoke or model training.")
    lines.append("- No paper-level evidence.")
    lines.append("- No H001 artifact modification.")
    lines.append("")
    lines.append("## Next")
    lines.append("")
    lines.append("```text")
    lines.append(NEXT_TODO)
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    errors: list[dict[str, Any]] = []
    scope_summary = load_required(args.scope_dir / "summary.json", errors, "scope_summary")
    train_summary = load_required(args.train_rga_summary, errors, "train_rga_summary")
    if scope_summary and train_summary:
        errors.extend(validate_inputs(scope_summary, train_summary))

    routes = route_rows(scope_summary, train_summary)
    probes = optional_probe_rows(train_summary)
    contract = target_contract(scope_summary, train_summary)
    risks = reviewer_risk_rows()
    audit_schema = audit_schema_rows()

    status = STATUS_ERROR if errors else STATUS_READY
    now = datetime.now(timezone.utc).isoformat()
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": now,
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
        "validation_error_path": rel_path(args.output_dir / "validation_errors.jsonl"),
        "boundary": {
            "split": "train_only_decision",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "input_artifacts": {
            "scope_summary": rel_path(args.scope_dir / "summary.json"),
            "train_rga_summary": rel_path(args.train_rga_summary),
        },
        "decision": {
            "selected_main_route": "support_contact_human_visual_mesh_audit_target",
            "selected_path": SELECTED_PATH,
            "why_not_relation_expansion_first": (
                "Relation expansion alone does not solve target independence; it is retained as a bounded optional probe."
            ),
            "why_not_relative_vertical_promotion_first": (
                "Relative vertical is clean but too narrow to resolve the H002 independent reliability target-source blocker."
            ),
            "optional_probe": "size_relative first; containment_inclusion second",
        },
        "target_source_contract": contract,
        "optional_probe_summary": {
            row["probe"]: {
                "predicates": row["predicates"],
                "gt_total": row["gt_total"],
                "recommended_role": row["recommended_role"],
            }
            for row in probes
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "target_source_contract.json", contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_csv(args.output_dir / "optional_relation_probe_plan.csv", probes)
    write_csv(args.output_dir / "audit_schema_contract.csv", audit_schema)
    write_csv(args.output_dir / "reviewer_risks.csv", risks)
    report = report_text(summary=summary, routes=routes, probes=probes, contract=contract, risks=risks)
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": SELECTED_PATH,
                "next_todo": NEXT_TODO,
                "validation_errors": len(errors),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
