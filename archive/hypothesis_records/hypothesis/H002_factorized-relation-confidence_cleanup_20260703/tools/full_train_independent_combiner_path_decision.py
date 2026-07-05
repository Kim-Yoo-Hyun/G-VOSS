#!/usr/bin/env python3
"""Decision artifact for the H002 combiner/posterior path."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_SMOKE = RGA_ROOT / "independent_combiner_upgrade_smoke_codex_ver/summary.json"
DEFAULT_ERROR = RGA_ROOT / "independent_combiner_upgrade_error_analysis_codex_ver/summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_combiner_path_decision_codex_ver"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-summary", type=Path, default=DEFAULT_SMOKE)
    parser.add_argument("--error-summary", type=Path, default=DEFAULT_ERROR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def decision_options() -> list[dict[str, Any]]:
    return [
        {
            "option_id": "A_negative_boundary",
            "decision": "not_selected",
            "meaning": "Stop posterior performance path and keep only RGA/mismatch benchmark framing.",
            "pros": "lowest reviewer risk; preserves current negative evidence honestly",
            "cons": "weakens method contribution around relation reliability posterior",
            "reason": "too conservative because C2/C3 showed structured partial signal",
        },
        {
            "option_id": "B_factor_revision_first",
            "decision": "selected",
            "meaning": (
                "Keep H002 active, but block posterior performance claims and revise "
                "relation-family-specific factors before any new combiner smoke."
            ),
            "pros": "matches observed failure mechanism; avoids generic classifier capacity story",
            "cons": "requires feature/factor redesign and another train-only smoke",
            "reason": (
                "C2/C3 partial gains are slice-specific: C2 ranking is not calibration-safe, "
                "and C3 is promising for relative_vertical/HL but hurts support_contact."
            ),
        },
        {
            "option_id": "C_target_revision_first",
            "decision": "not_selected_primary",
            "meaning": "Pause factor work and prioritize human-confirmed or redesigned target labels.",
            "pros": "addresses bootstrap-label risk directly",
            "cons": "does not explain the current family/direction failure mechanism",
            "reason": (
                "target risk remains real, but current failure points to factor/family behavior; "
                "target revision should remain a gate before paper claims, not the next design step."
            ),
        },
        {
            "option_id": "D_high_capacity_combiner",
            "decision": "rejected_for_now",
            "meaning": "Try monotonic GBDT, mixture-of-experts, or larger nonlinear combiner now.",
            "pros": "may improve metrics on the 158-row slice",
            "cons": "high overfit and weak method-necessity story",
            "reason": "current 158-row bootstrap target is too small and failure is factor-structured",
        },
    ]


def factor_revision_plan() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "factor": "support_contact_factor_split",
            "problem": "C2/C3 overcorrect support_contact and damage global AUPRC/calibration.",
            "revision": (
                "Separate floor/support contact, object-object support, and weak contact/no-contact "
                "evidence instead of using one generic p_geom_valid/disagreement signal."
            ),
            "next_check": "support_contact slice should stop dominating new threshold mistakes.",
        },
        {
            "priority": 2,
            "factor": "relative_vertical_order_residual",
            "problem": "C3 is promising for relative_vertical but the signal is mixed into a global gate.",
            "revision": (
                "Expose vertical ordering residual, vertical clearance, overlap/containment proxy, and "
                "direction-consistent sign features separately."
            ),
            "next_check": "relative_vertical gains should persist without harming support_contact.",
        },
        {
            "priority": 3,
            "factor": "coverage_uncertainty_factor",
            "problem": "C3 uses consistency as a weak proxy because explicit coverage is missing.",
            "revision": (
                "Add deployable coverage/missingness factors where available; keep multi-view as audit "
                "evidence until base posterior is supported."
            ),
            "next_check": "uncertainty gate should distinguish evidence absence from true contradiction.",
        },
        {
            "priority": 4,
            "factor": "family_shrinkage_gate",
            "problem": "C2 family gate is useful in some slices but overfits/overcorrects others.",
            "revision": (
                "Use family-specific residual scale with shrinkage and forbid per-predicate free models "
                "at the current label count."
            ),
            "next_check": "family-gated model should improve C2 ranking without worsening Brier.",
        },
        {
            "priority": 5,
            "factor": "target_confirmation_gate",
            "problem": "All current posterior results depend on Codex bootstrap labels.",
            "revision": (
                "Keep current labels as hypothesis-stage only; require human-confirmed or stronger "
                "independent labels before paper-level posterior claims."
            ),
            "next_check": "positive posterior smoke remains diagnostic until target confirmation.",
        },
    ]


def build_summary(smoke_summary: dict[str, Any], error_summary: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": "h002_full_train_independent_combiner_path_decision_summary_v0",
        "status": "full_train_independent_combiner_path_decision_factor_revision_first",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "smoke_summary": smoke.rel_path(DEFAULT_SMOKE),
            "smoke_status": smoke_summary.get("status"),
            "error_summary": smoke.rel_path(DEFAULT_ERROR),
            "error_status": error_summary.get("status"),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "hidden_metadata_used": False,
            "multi_view_used": False,
            "paper_evidence_allowed": False,
            "posterior_performance_claim_allowed": False,
            "generic_high_capacity_combiner_allowed_next": False,
        },
        "selected_path": "B_factor_revision_first",
        "decision_options": decision_options(),
        "factor_revision_plan": factor_revision_plan(),
        "decision": (
            "Keep H002 active, but freeze the current posterior performance result as a "
            "negative/partial boundary. Do not add a generic high-capacity combiner next. "
            "Revise relation-family-specific deployable factors first, then run another "
            "train-only smoke only if the revised factors address the observed support_contact "
            "and relative_vertical/HL failure mechanisms."
        ),
        "claim_boundary": {
            "allowed": (
                "RGA exposes semantic/geometric mismatch and shows that current posterior "
                "combiners have family-specific failure modes under a controlled train-only target."
            ),
            "blocked": (
                "factorized reliability posterior improves relation reliability over "
                "semantic_plus_geometry."
            ),
        },
        "next_todo": "full_train_independent_factor_revision_design",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Combiner Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only decision artifact.",
        "- No new model is trained here.",
        "- No validation/test rows are used.",
        "- Hidden audit metadata is not used.",
        "- Multi-view is not used as input.",
        "- Posterior performance claim remains blocked.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Options",
        "",
        "| Option | Decision | Reason |",
        "| --- | --- | --- |",
    ]
    for row in summary["decision_options"]:
        lines.append(f"| `{row['option_id']}` | `{row['decision']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Factor Revision Plan",
            "",
            "| Priority | Factor | Problem | Next Check |",
            "| ---: | --- | --- | --- |",
        ]
    )
    for row in summary["factor_revision_plan"]:
        lines.append(f"| {row['priority']} | `{row['factor']}` | {row['problem']} | {row['next_check']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"Allowed: {summary['claim_boundary']['allowed']}",
            "",
            f"Blocked: {summary['claim_boundary']['blocked']}",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    write_csv(
        output_dir / "decision_options.csv",
        summary["decision_options"],
        ["option_id", "decision", "meaning", "pros", "cons", "reason"],
    )
    write_csv(
        output_dir / "factor_revision_plan.csv",
        summary["factor_revision_plan"],
        ["priority", "factor", "problem", "revision", "next_check"],
    )
    write_report(output_dir / "decision.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    smoke_summary = read_json(args.smoke_summary)
    error_summary = read_json(args.error_summary)
    output_dir = smoke.as_abs(args.output_dir)
    summary = build_summary(smoke_summary, error_summary, output_dir)
    summary["input"]["smoke_summary"] = smoke.rel_path(args.smoke_summary)
    summary["input"]["error_summary"] = smoke.rel_path(args.error_summary)
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        "status={status} selected_path={selected_path} validation_used={validation_used} "
        "posterior_claim_allowed={posterior_claim_allowed} next={next_todo}".format(
            status=summary["status"],
            selected_path=summary["selected_path"],
            validation_used=summary["boundary"]["validation_usage"],
            posterior_claim_allowed=summary["boundary"]["posterior_performance_claim_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
