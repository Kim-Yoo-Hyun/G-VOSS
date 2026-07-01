#!/usr/bin/env python3
"""Synthesize two scoped H002 C_e results and select the next validation route."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RELATIVE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision"
DEFAULT_SUPPORT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan"

EXPECTED_RELATIVE_STATUS = "h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe"
EXPECTED_SUPPORT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_input_errors"
SELECTED_PATH = "freeze_two_family_Ce_claim_select_independent_validity_target_plan"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_target_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relative-dir", type=Path, default=DEFAULT_RELATIVE_DIR)
    parser.add_argument("--support-dir", type=Path, default=DEFAULT_SUPPORT_DIR)
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
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def mechanism(summary: dict[str, Any]) -> dict[str, Any]:
    return summary.get("mechanism_result", {})


def validate_input(name: str, summary: dict[str, Any], expected_status: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != expected_status:
        errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
    if summary.get("validation_errors") != 0:
        errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
    mech = mechanism(summary)
    if mech.get("accepted") is not True:
        errors.append({"input": name, "error_type": "mechanism_not_accepted", "actual": mech.get("accepted")})
    if float(mech.get("primary_auroc", 0.0)) < 0.90:
        errors.append({"input": name, "error_type": "primary_auc_below_gate", "actual": mech.get("primary_auroc")})
    if float(mech.get("geometry_only_auroc", 1.0)) > 0.60:
        errors.append({"input": name, "error_type": "geometry_only_above_gate", "actual": mech.get("geometry_only_auroc")})
    if float(mech.get("plain_concat_auroc", 1.0)) > 0.60:
        errors.append({"input": name, "error_type": "plain_concat_above_gate", "actual": mech.get("plain_concat_auroc")})
    if float(mech.get("wrong_t_auroc", 1.0)) > 0.60:
        errors.append({"input": name, "error_type": "wrong_t_above_gate", "actual": mech.get("wrong_t_auroc")})
    if float(mech.get("shuffled_g_global_auroc", 1.0)) > 0.60:
        errors.append({"input": name, "error_type": "shuffled_g_global_above_gate", "actual": mech.get("shuffled_g_global_auroc")})
    if float(mech.get("shuffled_g_within_predicate_auroc", 1.0)) > 0.60:
        errors.append(
            {
                "input": name,
                "error_type": "shuffled_g_within_predicate_above_gate",
                "actual": mech.get("shuffled_g_within_predicate_auroc"),
            }
        )

    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"input": name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def family_evidence_rows(relative: dict[str, Any], support: dict[str, Any]) -> list[dict[str, Any]]:
    r = mechanism(relative)
    s = mechanism(support)
    return [
        {
            "family": "relative_vertical",
            "predicates": "higher than; lower than",
            "geometry_evidence": "signed vertical object-pair OBB geometry",
            "target_form": "same-G_e predicate flip",
            "rows": 400,
            "primary_model": r.get("primary_model"),
            "primary_auroc": r.get("primary_auroc"),
            "geometry_only_auroc": r.get("geometry_only_auroc"),
            "plain_concat_auroc": r.get("plain_concat_auroc"),
            "wrong_t_auroc": r.get("wrong_t_auroc"),
            "shuffled_g_auroc": f"{r.get('shuffled_g_global_auroc')} / {r.get('shuffled_g_within_predicate_auroc')}",
            "claim_role": "first scoped C_e mechanism proof",
            "main_caveat": "controlled vertical compatibility, not final reliability",
        },
        {
            "family": "support_contact_pose_conditioned",
            "predicates": "lying on; standing on",
            "geometry_evidence": "pose/orientation/contact/overlap/gap semseg features plus optional point-contact Q_e",
            "target_form": "same-G_e pose-conditioned predicate flip",
            "rows": s.get("counts", {}).get("rows", 400),
            "primary_model": s.get("primary_model"),
            "primary_auroc": s.get("primary_auroc"),
            "geometry_only_auroc": s.get("geometry_only_auroc"),
            "plain_concat_auroc": s.get("plain_concat_auroc"),
            "wrong_t_auroc": s.get("wrong_t_auroc"),
            "shuffled_g_auroc": f"{s.get('shuffled_g_global_auroc')} / {s.get('shuffled_g_within_predicate_auroc')}",
            "claim_role": "second scoped C_e mechanism proof",
            "main_caveat": "constructed pose-compatibility target, not human reliability",
        },
    ]


def reviewer_risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "constructed_target",
            "severity": "high",
            "reviewer_question": "Are the targets just synthetic rules rather than relation reliability?",
            "current_answer": "Yes, the current evidence is scoped C_e mechanism proof only.",
            "required_next": "Build an independent validity target using GT, human/audit, or high-precision non-construction labels.",
        },
        {
            "risk": "too_clean_auc",
            "severity": "medium",
            "reviewer_question": "Does AUROC 1.0 mean the target is too easy?",
            "current_answer": "It is intentionally clean to isolate the mechanism.",
            "required_next": "Evaluate on harder mixed strata where C_e must help beyond obvious construction.",
        },
        {
            "risk": "limited_family_scope",
            "severity": "medium",
            "reviewer_question": "Does this generalize beyond vertical/support-contact?",
            "current_answer": "Not yet. It spans two physical families but not all 3DSSG relations.",
            "required_next": "Decide between external validity first and a third family after the independent target plan.",
        },
        {
            "risk": "no_final_reliability",
            "severity": "high",
            "reviewer_question": "Where are p_obs and p_rel results?",
            "current_answer": "Current results validate C_e, not final selective reliability.",
            "required_next": "Define p_obs/p_rel target only after independent relation validity labels are available.",
        },
        {
            "risk": "not_docker_paper_evidence",
            "severity": "high",
            "reviewer_question": "Can this be reproduced as a paper experiment?",
            "current_answer": "No. This is train-only hypothesis-stage evidence.",
            "required_next": "Promote to Docker only after claim scope and independent target are frozen.",
        },
    ]


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "add_attachment_or_proximity_immediately",
            "verdict": "defer",
            "reason": "Another family may increase artifact count but will not resolve the controlled-target caveat.",
            "next_action": "return after independent validity target design",
        },
        {
            "route": "promote_two_family_Ce_as_broad_reliability",
            "verdict": "reject",
            "reason": "Two controlled C_e targets do not establish p_rel, p_obs, or human/GT reliability.",
            "next_action": "keep broad reliability blocked",
        },
        {
            "route": "freeze_two_family_Ce_claim",
            "verdict": "selected",
            "reason": "Both families show the same mechanism: G_e alone is insufficient, and aligned T_e-G_e interaction is necessary.",
            "next_action": "use as H002 mechanism core",
        },
        {
            "route": "independent_validity_target_before_more_families",
            "verdict": "selected_next",
            "reason": "The dominant reviewer risk is target independence, not absence of a third constructed family.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "docker_promotion_now",
            "verdict": "defer",
            "reason": "Docker promotion before independent validity would reproduce a scoped smoke, not a paper-level reliability result.",
            "next_action": "write Docker prerequisites but do not create experiment root yet",
        },
    ]


def claim_boundary() -> dict[str, Any]:
    return {
        "allowed_claim": (
            "Across relative-vertical and support/contact pose-conditioned relation families, "
            "predicate-independent geometry evidence G_e is not sufficient by itself; relation "
            "compatibility requires an explicit semantic-geometry compatibility factor C_e that "
            "conditions geometry interpretation on semantic content T_e."
        ),
        "short_claim": "two-family predicate-geometry compatibility mechanism proof",
        "not_allowed": [
            "broad 3D scene graph relation reliability",
            "final p_rel / p_obs decision quality",
            "human-audited relation reliability performance",
            "all relation-family generality",
            "paper-level Docker reproduced evidence",
        ],
        "claim_type": "hypothesis-stage mechanism evidence",
    }


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Design an independent train-side validity target that tests whether C_e helps on relation validity beyond constructed same-G_e compatibility labels.",
        "candidate_targets": [
            "GT relation match versus C_e support/conflict",
            "human/audit accept-reject subset with hidden construction fields excluded",
            "high-precision cross-source agreement plus geometry-supported positive anchors",
            "wrong-pair or predicate-flip hard negatives matched by source rank, object family, and coverage",
        ],
        "required_controls": [
            "source-only Z_e",
            "semantic-only T_e",
            "geometry-only G_e",
            "plain T_e + G_e concat",
            "interaction C_e",
            "wrong-T same-G control",
            "shuffled-G within-family control",
            "same-rank and same-object-family control",
        ],
        "do_not_do_next": [
            "Do not treat no-GT as automatic negative.",
            "Do not use validation/test rows for hypothesis-stage target construction.",
            "Do not use construction labels or hidden target proxies as model input.",
            "Do not promote p_rel/p_obs until the independent target has class mass and shortcut controls.",
        ],
        "success_condition": [
            "explicit label source independent from the constructed same-G_e target",
            "minimum class mass for accept/reject or compatibility-supported/conflicting rows",
            "shortcut audit plan before learned smoke",
            "decision whether p_rel/p_obs can be tested or remains blocked",
            "clear Docker promotion prerequisites",
        ],
    }


def build_decision(relative: dict[str, Any], support: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_compatibility_dataset_v3_multi_family_synthesis_inputs"
    selected_path = SELECTED_PATH if not errors else "fix_inputs_before_synthesis"
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "split": "train_only_synthesis_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "claim_boundary": claim_boundary(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "family_evidence_table": family_evidence_rows(relative, support),
        "input_artifacts": {
            "relative_vertical": rel_path(DEFAULT_RELATIVE_DIR),
            "support_contact_pose_conditioned": rel_path(DEFAULT_SUPPORT_DIR),
        },
        "next_plan_contract": next_plan_contract(),
        "next_todo": next_todo,
        "reviewer_risk_table": reviewer_risk_rows(),
        "route_table": route_rows(),
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(errors),
    }


def build_report(decision: dict[str, Any]) -> str:
    lines = [
        "# H002 Multi-Family Result Synthesis Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {decision['status']}",
        f"selected_path = {decision['selected_path']}",
        f"validation_errors = {decision['validation_errors']}",
        f"next_todo = {decision['next_todo']}",
        "```",
        "",
        "## Synthesis Decision",
        "",
        "Allowed claim:",
        "",
        "```text",
        decision["claim_boundary"]["allowed_claim"],
        "```",
        "",
        "The current H002 evidence is a two-family `C_e` mechanism proof. It is not a broad",
        "relation-reliability result.",
        "",
        "## Family Evidence",
        "",
        "| Family | Predicates | Primary AUROC | G-only AUROC | Plain Concat AUROC | Control Summary | Claim Role |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in decision["family_evidence_table"]:
        lines.append(
            f"| `{row['family']}` | {row['predicates']} | `{row['primary_auroc']}` | "
            f"`{row['geometry_only_auroc']}` | `{row['plain_concat_auroc']}` | "
            f"wrong-T `{row['wrong_t_auroc']}`, shuffled-G `{row['shuffled_g_auroc']}` | {row['claim_role']} |"
        )

    lines.extend(
        [
            "",
            "## Reviewer Risks",
            "",
            "| Risk | Severity | Current Answer | Required Next |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in decision["reviewer_risk_table"]:
        lines.append(f"| `{row['risk']}` | `{row['severity']}` | {row['current_answer']} | {row['required_next']} |")

    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            "| Route | Verdict | Reason | Next Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in decision["route_table"]:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} | `{row['next_action']}` |")

    lines.extend(
        [
            "",
            "## Next Plan Contract",
            "",
            "The next stage should design an independent train-side validity target before adding",
            "attachment, proximity, or horizontal families.",
            "",
            "Candidate targets:",
            "",
        ]
    )
    for item in decision["next_plan_contract"]["candidate_targets"]:
        lines.append(f"- {item}")
    lines.extend(["", "Required controls:", ""])
    for item in decision["next_plan_contract"]["required_controls"]:
        lines.append(f"- {item}")
    lines.extend(["", "Success condition:", ""])
    for item in decision["next_plan_contract"]["success_condition"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only H002 synthesis plan.",
            "- No validation/test usage.",
            "- No new learned model trained in this step.",
            "- No H001 artifact modification.",
            "- No paper-level evidence promotion.",
            "",
            "## Next",
            "",
            "```text",
            decision["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    relative = read_json(args.relative_dir / "summary.json")
    support = read_json(args.support_dir / "summary.json")
    errors = []
    errors.extend(validate_input("relative_vertical", relative, EXPECTED_RELATIVE_STATUS))
    errors.extend(validate_input("support_contact_pose_conditioned", support, EXPECTED_SUPPORT_STATUS))

    decision = build_decision(relative, support, errors)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(output_dir / "claim_boundary.json", decision["claim_boundary"])
    write_json(output_dir / "next_plan_contract.json", decision["next_plan_contract"])
    write_csv(output_dir / "family_evidence_table.csv", decision["family_evidence_table"])
    write_csv(output_dir / "reviewer_risk_table.csv", decision["reviewer_risk_table"])
    write_csv(output_dir / "route_table.csv", decision["route_table"])
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(decision), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
