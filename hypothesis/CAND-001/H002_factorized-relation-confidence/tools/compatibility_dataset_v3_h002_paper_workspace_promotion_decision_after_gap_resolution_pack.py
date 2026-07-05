#!/usr/bin/env python3
"""Create the H002 paper-workspace promotion decision artifact.

This is a documentation/provenance gate. It does not run metrics and does not
edit the active H001 manuscript.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
H2_ROOT = REPO_ROOT / "hypothesis/CAND-001/H002_factorized-relation-confidence"
INPUT_GAP_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review"
INPUT_POBS_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner"
OUTPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack"
PAPER_WORKSPACE = REPO_ROOT / "paper/h002_compatibility_routing"

SCHEMA_VERSION = "h002_paper_workspace_promotion_decision_after_gap_resolution_pack_v1"
STATUS_READY = "h002_paper_workspace_promotion_decision_after_gap_resolution_pack_ready"
STATUS_ERROR = "h002_paper_workspace_promotion_decision_after_gap_resolution_pack_input_errors"
NEXT_TODO = "h002_paper_workspace_initial_draft_and_figure_table_sync"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(gap: dict, pobs: dict) -> list[dict]:
    errors: list[dict] = []
    expected_gap_status = "h002_gap_resolution_pack_after_outline_review_ready"
    expected_pobs_status = "h002_pobs_prel_calibration_upgrade_result_review_after_runner_ready"
    expected_gap_next = "compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack"

    if gap.get("status") != expected_gap_status:
        errors.append({"error_type": "unexpected_gap_status", "actual": gap.get("status")})
    if gap.get("validation_errors") != 0:
        errors.append({"error_type": "gap_validation_errors_nonzero", "actual": gap.get("validation_errors")})
    if gap.get("next_todo") != expected_gap_next:
        errors.append({"error_type": "unexpected_gap_next_todo", "actual": gap.get("next_todo")})

    for key in [
        "claim_thesis_resolved",
        "main_result_ci_resolved",
        "table_ablation_contract_resolved",
        "figure_spec_resolved",
        "related_work_novelty_map_resolved",
        "failure_taxonomy_resolved",
    ]:
        if gap.get(key) is not True:
            errors.append({"error_type": "gap_not_resolved", "field": key, "actual": gap.get(key)})

    if gap.get("official_test_claim_allowed") is not False:
        errors.append({"error_type": "official_test_claim_unexpectedly_allowed"})
    if gap.get("sota_or_leaderboard_claim_allowed") is not False:
        errors.append({"error_type": "sota_claim_unexpectedly_allowed"})

    if pobs.get("status") != expected_pobs_status:
        errors.append({"error_type": "unexpected_pobs_status", "actual": pobs.get("status")})
    if pobs.get("validation_errors") != 0:
        errors.append({"error_type": "pobs_validation_errors_nonzero", "actual": pobs.get("validation_errors")})
    if pobs.get("calibrated_quantitative_claim_pass") is not False:
        errors.append({"error_type": "pobs_calibrated_claim_unexpectedly_passed"})

    return errors


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    gap_summary = read_json(INPUT_GAP_ROOT / "summary.json")
    pobs_summary = read_json(INPUT_POBS_ROOT / "summary.json")
    errors = validate_inputs(gap_summary, pobs_summary)
    status = STATUS_ERROR if errors else STATUS_READY

    selected_path = (
        "promote_h002_to_dedicated_paper_workspace_no_h001_manuscript_edit_validation_main_claim"
        if not errors
        else "fix_inputs_before_workspace_promotion"
    )

    decision_rows = [
        {
            "decision": "promote_to_dedicated_h002_paper_workspace",
            "value": "true" if not errors else "false",
            "reason": "gap-resolution pack is complete and user asked to proceed with the next H002 TODO",
        },
        {
            "decision": "edit_h001_manuscript_now",
            "value": "false",
            "reason": "H002 is separated from H001; H001 paper source remains untouched by this gate",
        },
        {
            "decision": "use_validation_table_as_main_h002_claim",
            "value": "true" if not errors else "false",
            "reason": "H002 compares VL-SAT/Open3DSG validation predictions on the official 3DSSG validation split",
        },
        {
            "decision": "claim_official_test_or_sota",
            "value": "false",
            "reason": "3DSSG relation test GT/eval-server provenance is not available in this branch",
        },
        {
            "decision": "claim_calibrated_pobs_prel_solved",
            "value": "false",
            "reason": "p_rel calibration worsened, observability negatives are absent, and attachment/containment rows are absent",
        },
    ]

    workspace_rows = [
        {
            "path": "paper/h002_compatibility_routing/README.md",
            "role": "H002 paper-workspace entry point and claim boundary",
            "required": "true",
        },
        {
            "path": "paper/h002_compatibility_routing/outline.md",
            "role": "section-level paper outline",
            "required": "true",
        },
        {
            "path": "paper/h002_compatibility_routing/draft.md",
            "role": "initial manuscript skeleton",
            "required": "true",
        },
        {
            "path": "paper/h002_compatibility_routing/tables.md",
            "role": "main/appendix table plan and source artifacts",
            "required": "true",
        },
        {
            "path": "paper/h002_compatibility_routing/figures.md",
            "role": "figure plan and artifact sources",
            "required": "true",
        },
        {
            "path": "paper/h002_compatibility_routing/risk.md",
            "role": "reviewer-risk register for H002",
            "required": "true",
        },
    ]

    claim_boundary_rows = [
        {"claim": "validation_source_reranking", "status": "allowed", "wording": "official 3DSSG validation split, VL-SAT/Open3DSG validation predictions"},
        {"claim": "open3dsg_open_vocab_source", "status": "allowed_with_caveat", "wording": "open-vocabulary source, closed-vocabulary 3DSSG mapping for quantitative Recall@K"},
        {"claim": "violation_metric", "status": "allowed_with_caveat", "wording": "H002 custom geometry-consistency metric"},
        {"claim": "pobs_prel_framework_layer", "status": "allowed", "wording": "selective-decision framework component and stress-test evidence"},
        {"claim": "official_test_benchmark", "status": "blocked", "wording": "do not claim official test result"},
        {"claim": "sota_or_leaderboard", "status": "blocked", "wording": "do not claim SOTA or leaderboard standing"},
        {"claim": "calibrated_pobs_prel_solved", "status": "blocked", "wording": "do not claim calibrated p_obs/p_rel reliability is solved"},
        {"claim": "support_contact_solved", "status": "blocked", "wording": "use support/contact as failure taxonomy, not success evidence"},
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_path": selected_path,
        "paper_workspace": "paper/h002_compatibility_routing",
        "h001_manuscript_edit_now": False,
        "new_top_level_paper_folder_created": False,
        "h002_paper_workspace_created": not errors,
        "main_validation_claim_allowed": not errors,
        "official_test_claim_allowed": False,
        "sota_or_leaderboard_claim_allowed": False,
        "pobs_prel_framework_component_allowed": True,
        "pobs_prel_calibrated_quantitative_claim_allowed": False,
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO if not errors else "fix_h002_paper_workspace_promotion_inputs",
    }

    write_json(OUTPUT_ROOT / "summary.json", summary)
    write_csv(OUTPUT_ROOT / "decision_matrix.csv", decision_rows)
    write_csv(OUTPUT_ROOT / "workspace_manifest.csv", workspace_rows)
    write_csv(OUTPUT_ROOT / "claim_boundary.csv", claim_boundary_rows)
    write_csv(OUTPUT_ROOT / "validation_errors.jsonl", errors)
    (OUTPUT_ROOT / "validation_errors.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
        encoding="utf-8",
    )

    report = "\n".join(
        [
            "# H002 Paper Workspace Promotion Decision",
            "",
            "## Decision",
            "",
            f"- status: `{status}`",
            f"- selected path: `{selected_path}`",
            f"- paper workspace: `paper/h002_compatibility_routing/`",
            "- H001 manuscript edit now: `false`",
            "- new top-level paper folder: `false`",
            "",
            "## Claim Boundary",
            "",
            "- Allowed: validation-level H002 source reranking on VL-SAT/Open3DSG validation predictions.",
            "- Allowed: p_obs/p_rel as a selective-decision framework component.",
            "- Blocked: official-test, SOTA, leaderboard, solved support/contact, and calibrated p_obs/p_rel solved claims.",
            "",
            "## Required Workspace Files",
            "",
            "| Path | Role |",
            "| --- | --- |",
            *[f"| `{row['path']}` | {row['role']} |" for row in workspace_rows],
            "",
            f"Validation errors: `{len(errors)}`",
        ]
    )
    (OUTPUT_ROOT / "report.md").write_text(report + "\n", encoding="utf-8")

    stage_file = H2_ROOT / "compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack.md"
    stage_file.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack",
                "",
                f"status = {status}",
                "artifact_root = hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack/",
                f"selected_path = {selected_path}",
                "paper_workspace = paper/h002_compatibility_routing/",
                "h001_manuscript_edit_now = false",
                "new_top_level_paper_folder_created = false",
                f"validation_errors = {len(errors)}",
                f"next_todo = {summary['next_todo']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
