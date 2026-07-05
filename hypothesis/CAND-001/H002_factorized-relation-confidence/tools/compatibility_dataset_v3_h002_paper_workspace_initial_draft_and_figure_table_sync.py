#!/usr/bin/env python3
"""Validate the promoted H002 paper workspace after route-aware goal update."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
H2_ROOT = REPO_ROOT / "hypothesis/CAND-001/H002_factorized-relation-confidence"
PAPER_ROOT = REPO_ROOT / "paper/h002_compatibility_routing"
PROMOTION_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack"
OUTPUT_ROOT = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync"

SCHEMA_VERSION = "h002_paper_workspace_initial_draft_and_figure_table_sync_v1"
STATUS_READY = "h002_paper_workspace_initial_draft_and_figure_table_sync_ready"
STATUS_ERROR = "h002_paper_workspace_initial_draft_and_figure_table_sync_input_errors"
NEXT_TODO = "h002_source_reranking_ablation_expansion_plan_after_route_goal_update"


REQUIRED_FILES = [
    "README.md",
    "outline.md",
    "draft.md",
    "tables.md",
    "figures.md",
    "risk.md",
    "route_framework.md",
]


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


def validate() -> list[dict]:
    errors: list[dict] = []

    promotion_summary = read_json(PROMOTION_ROOT / "summary.json")
    if promotion_summary.get("status") != "h002_paper_workspace_promotion_decision_after_gap_resolution_pack_ready":
        errors.append({"error_type": "unexpected_promotion_status", "actual": promotion_summary.get("status")})
    if promotion_summary.get("validation_errors") != 0:
        errors.append({"error_type": "promotion_validation_errors_nonzero", "actual": promotion_summary.get("validation_errors")})

    for filename in REQUIRED_FILES:
        path = PAPER_ROOT / filename
        if not path.exists():
            errors.append({"error_type": "missing_paper_file", "path": str(path.relative_to(REPO_ROOT))})
            continue
        text = path.read_text(encoding="utf-8")
        if filename in {"README.md", "outline.md", "draft.md", "route_framework.md"}:
            for phrase in ["route-aware", "support/contact", "p_obs"]:
                if phrase not in text:
                    errors.append({"error_type": "missing_route_aware_phrase", "file": filename, "phrase": phrase})
        if filename == "tables.md":
            for phrase in ["Route Readiness", "source x geometry-only", "source x T+G concat"]:
                if phrase not in text:
                    errors.append({"error_type": "missing_table_sync_phrase", "file": filename, "phrase": phrase})
        if filename == "risk.md" and "Route-Aware Framework Looks Like Future Work" not in text:
            errors.append({"error_type": "missing_route_aware_risk", "file": filename})

    return errors


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    errors = validate()
    status = STATUS_ERROR if errors else STATUS_READY

    route_rows = [
        {
            "route": "comparison_compatibility",
            "relation_types": "higher/lower,bigger/smaller",
            "current_status": "main_quantitative_success",
            "paper_role": "primary claim evidence",
            "next_experiment": "source_x_geometry_only_and_source_x_concat_ablation",
        },
        {
            "route": "geometry_only_compatibility",
            "relation_types": "close_by,near",
            "current_status": "control_generality_route",
            "paper_role": "route-aware generality/control",
            "next_experiment": "optional source-level proximity route table",
        },
        {
            "route": "frame_aware_directional",
            "relation_types": "left/right/front/behind",
            "current_status": "candidate_route_with_frame_risk",
            "paper_role": "future or appendix unless frame controls pass",
            "next_experiment": "frame_robustness_and_violation_control",
        },
        {
            "route": "support_contact",
            "relation_types": "standing_on,lying_on,supported_by",
            "current_status": "hard_route_failure_taxonomy",
            "paper_role": "limitation and design-necessity evidence",
            "next_experiment": "richer_contact_pose_mesh_Ge",
        },
        {
            "route": "observability_heavy",
            "relation_types": "attached_to,hanging_on,connected_to,inside,cover",
            "current_status": "future_route",
            "paper_role": "p_obs/Q_e motivation and future route",
            "next_experiment": "real_visual_mesh_Qe_labels_before_model_input",
        },
        {
            "route": "semantic_structural",
            "relation_types": "part_of,belonging_to,same_as,same_symmetry_as",
            "current_status": "separate_or_abstain_route",
            "paper_role": "scope boundary",
            "next_experiment": "not_current_main_experiment",
        },
    ]

    sync_rows = [
        {
            "item": "goal_update",
            "status": "complete" if not errors else "blocked",
            "decision": "H002 goal is route-aware reliable 3D relation framework, not universal scalar scorer.",
        },
        {
            "item": "current_main_claim",
            "status": "narrowed",
            "decision": "Main quantitative success is comparison compatibility route on official validation.",
        },
        {
            "item": "generality_boundary",
            "status": "explicit",
            "decision": "Other relation families are route map / hard route / future route, not solved claims.",
        },
        {
            "item": "next_experiment",
            "status": "selected",
            "decision": "Add source x geometry-only and source x concat reranking ablations before broadening claim.",
        },
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_workspace": "paper/h002_compatibility_routing",
        "goal": "relation_aware_reliable_3d_relation_framework",
        "current_main_success_route": "comparison_compatibility",
        "current_main_success_relations": ["relative_vertical", "size_relative"],
        "support_contact_status": "hard_route_failure_taxonomy",
        "pobs_prel_status": "framework_component_not_calibrated_solved_claim",
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO if not errors else "fix_h002_paper_workspace_route_goal_sync",
    }

    write_json(OUTPUT_ROOT / "summary.json", summary)
    write_csv(OUTPUT_ROOT / "route_readiness.csv", route_rows)
    write_csv(OUTPUT_ROOT / "sync_decision.csv", sync_rows)
    (OUTPUT_ROOT / "validation_errors.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in errors),
        encoding="utf-8",
    )

    report_lines = [
        "# H002 Paper Workspace Initial Sync",
        "",
        "## Decision",
        "",
        f"- status: `{status}`",
        "- goal: `relation_aware_reliable_3d_relation_framework`",
        "- current main success route: `comparison_compatibility`",
        "- current main success relations: `relative_vertical`, `size_relative`",
        "- support/contact: hard-route failure taxonomy",
        "- p_obs/p_rel: framework component, not calibrated solved claim",
        "",
        "## Next Experiment",
        "",
        "`source x geometry-only` and `source x T+G concat` reranking ablations should be added before broadening the paper claim.",
        "",
        f"Validation errors: `{len(errors)}`",
    ]
    (OUTPUT_ROOT / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    stage_file = H2_ROOT / "compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync.md"
    stage_file.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync",
                "",
                f"status = {status}",
                "artifact_root = hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_h002_paper_workspace_initial_draft_and_figure_table_sync/",
                "goal = relation_aware_reliable_3d_relation_framework",
                "current_main_success_route = comparison_compatibility",
                "current_main_success_relations = relative_vertical,size_relative",
                "support_contact_status = hard_route_failure_taxonomy",
                "pobs_prel_status = framework_component_not_calibrated_solved_claim",
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
