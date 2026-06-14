#!/usr/bin/env python3
"""Freeze H002 validation plan for the current factorized posterior."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_MULTIVIEW_SUMMARY = RGA_ROOT / "multiview_audit_protocol/summary.json"
DEFAULT_CODEX_SMOKE_SUMMARY = RGA_ROOT / "codex_label_smoke/summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "factorized_validation_plan"


BASELINES = {
    "semantic_only": {
        "inputs": ["S_e"],
        "role": "tests whether source score/rank alone explains reliability labels",
    },
    "geometry_only": {
        "inputs": ["G_e"],
        "role": "tests whether 3D geometry evidence alone explains reliability labels",
    },
    "semantic_plus_geometry": {
        "inputs": ["S_e", "G_e"],
        "role": "strong simple baseline; factorized posterior must beat this to support H002",
    },
    "factorized_reliability_posterior": {
        "inputs": ["S_e", "G_e", "C_e", "U_e"],
        "role": "current H002 method candidate; V_mv_e is explicitly excluded",
    },
}

FEATURE_POLICY = {
    "allowed_now": [
        "semantic_score_raw",
        "semantic_score_norm_or_rank_with_rank_band_control",
        "continuous_geometry_evidence",
        "p_geom_valid",
        "coverage_state_or_checkability",
        "uncertainty_or_abstain_state",
    ],
    "excluded_from_claim_view": [
        "working_label",
        "final_human_label",
        "codex_ver_label",
        "visual_audit_decision",
        "reviewer_id",
        "RGA bucket identity such as top100_and_unsatisfied",
        "target construction flags such as tail_gt100_and_satisfied",
        "predicate label/family when not controlled by stratification",
        "V_mv_e deployable visual features",
    ],
    "diagnostic_only": [
        "full_factorized view with direct identity features",
        "cross-family pooled view before per-family controls",
        "codex_ver label smoke",
    ],
}

TARGET_REQUIREMENTS = {
    "hypothesis_stage_minimum": {
        "label_source": "human-confirmed or independent audit labels; codex_ver is not enough",
        "usable_binary_rows_min": 60,
        "per_class_min": 20,
        "reviewers": 1,
        "preferred_reviewers": 2,
        "primary_target": "same-family, same-geometry-status, same-rank-band reliability labels",
        "allowed_use": "train-only hypothesis validation, not paper result",
    },
    "paper_prep_minimum": {
        "label_source": "two reviewers or adjudicated conflicts",
        "usable_binary_rows_min": 100,
        "per_class_min": 40,
        "agreement": ">=0.75 exact final-label agreement or adjudicated disagreements",
        "required_later": "held-out validation/test only after target and feature policy freeze",
    },
}

CONTROL_PLAN = {
    "same_family": {
        "purpose": "avoid family/source shortcut",
        "required_for_claim": True,
        "implementation": "evaluate within one predicate family first; pooled cross-family results are diagnostic",
    },
    "same_geometry_status": {
        "purpose": "avoid satisfied vs unsatisfied shortcut",
        "required_for_claim": True,
        "implementation": "primary target should compare reliability labels within geometry_status=satisfied",
    },
    "same_rank_band": {
        "purpose": "avoid top-K vs tail semantic shortcut",
        "required_for_claim": True,
        "implementation": "sample or stratify positives/negatives within rank bands before crossfit",
    },
    "same_source": {
        "purpose": "avoid source/domain shortcut",
        "required_for_current_train_pilot": True,
        "implementation": "current plan uses Open3DSG train pilot only; cross-source evidence is later",
    },
    "no_visual_input": {
        "purpose": "keep V_mv_e deferred",
        "required_for_current_gate": True,
        "implementation": "visual/multiview fields can affect labels but cannot enter model features",
    },
}

ACCEPTANCE_RULE = {
    "hypothesis_support_signal": [
        "labels pass hypothesis_stage_minimum",
        "all required controls pass structurally",
        "factorized_reliability_posterior beats semantic_plus_geometry on AUPRC by >=0.03 or Brier by <=-0.02",
        "no AUROC drop larger than 0.02 relative to semantic_plus_geometry",
        "gain remains after direct identity/rga-bucket features are removed",
        "gain is not concentrated in one obvious artifact stratum",
    ],
    "strong_support_signal": [
        "above conditions hold with two-reviewer/adjudicated labels",
        "bootstrap confidence interval for factorized minus semantic_plus_geometry is positive for AUPRC or negative for Brier",
        "coverage/uncertainty ablation shows C_e/U_e contribute beyond S_e+G_e",
    ],
    "stop_or_reframe": [
        "factorized is indistinguishable from semantic_plus_geometry",
        "gains disappear under same-family/status/rank controls",
        "label target remains codex_ver or machine-assisted only",
        "performance is explained by predicate family, rank bucket, or geometry status identity",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--multiview-summary", type=Path, default=DEFAULT_MULTIVIEW_SUMMARY)
    parser.add_argument("--codex-smoke-summary", type=Path, default=DEFAULT_CODEX_SMOKE_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def baseline_metrics(codex_summary: dict[str, Any]) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for row in codex_summary.get("metric_rows", []):
        if row.get("kind") != "baseline":
            continue
        if row.get("split_eval") != "train_internal_5fold":
            continue
        metrics = row["metrics"]
        output[row["name"]] = {
            "auroc": metrics["auroc"],
            "auprc": metrics["auprc"],
            "brier": metrics["brier"],
            "ece_5bin": metrics["ece_5bin"],
            "accuracy_at_0_5": metrics["accuracy_at_0_5"],
        }
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Factorized Validation Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Current gate validates `P(R_e = 1 | S_e, G_e, C_e, U_e)` only.",
        "- `V_mv_e` is not a model input.",
        "- No validation/test rows are used.",
        "- Codex labels are plumbing evidence only.",
        "",
        "## Current Smoke Reference",
        "",
        "| Baseline | AUROC | AUPRC | Brier |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, metrics in summary["reference_codex_smoke_metrics"].items():
        lines.append(f"| `{name}` | {metrics['auroc']:.4f} | {metrics['auprc']:.4f} | {metrics['brier']:.4f} |")
    lines.extend(
        [
            "",
            "These numbers do not establish posterior advantage because labels are `(codex_ver)`",
            "and the target has only 27 rows.",
            "",
            "## Target Minimum",
            "",
            "| Gate | Rows | Per class | Label source |",
            "| --- | ---: | ---: | --- |",
            (
                f"| hypothesis-stage | {TARGET_REQUIREMENTS['hypothesis_stage_minimum']['usable_binary_rows_min']} | "
                f"{TARGET_REQUIREMENTS['hypothesis_stage_minimum']['per_class_min']} | "
                f"{TARGET_REQUIREMENTS['hypothesis_stage_minimum']['label_source']} |"
            ),
            (
                f"| paper-prep | {TARGET_REQUIREMENTS['paper_prep_minimum']['usable_binary_rows_min']} | "
                f"{TARGET_REQUIREMENTS['paper_prep_minimum']['per_class_min']} | "
                f"{TARGET_REQUIREMENTS['paper_prep_minimum']['label_source']} |"
            ),
            "",
            "## Required Controls",
            "",
            "| Control | Required | Purpose |",
            "| --- | --- | --- |",
        ]
    )
    for name, spec in CONTROL_PLAN.items():
        required = spec.get("required_for_claim") or spec.get("required_for_current_gate") or spec.get("required_for_current_train_pilot")
        lines.append(f"| `{name}` | `{bool(required)}` | {spec['purpose']} |")
    lines.extend(
        [
            "",
            "## Acceptance Rule",
            "",
            "Factorized posterior can support the H002 hypothesis only if it beats",
            "`semantic_plus_geometry` under controlled, human-confirmed labels and the gain",
            "does not come from family/status/rank shortcuts.",
            "",
            "Next gate: `36_controlled_label_target.md`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    multiview = read_json(args.multiview_summary)
    codex = read_json(args.codex_smoke_summary)
    created_at = datetime.now(timezone.utc).isoformat()
    paths = {
        "summary": output_dir / "summary.json",
        "protocol": output_dir / "protocol.json",
        "report": output_dir / "report.md",
    }
    protocol = {
        "schema_version": "h002_factorized_validation_protocol_v0",
        "posterior_under_validation": "P(R_e = 1 | S_e, G_e, C_e, U_e)",
        "future_deferred_posterior": "P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)",
        "baselines": BASELINES,
        "feature_policy": FEATURE_POLICY,
        "target_requirements": TARGET_REQUIREMENTS,
        "control_plan": CONTROL_PLAN,
        "acceptance_rule": ACCEPTANCE_RULE,
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "paper_result": False,
            "vmv_model_input_allowed": False,
            "codex_ver_sufficient_for_claim": False,
        },
    }
    summary = {
        "schema_version": "h002_factorized_validation_plan_summary_v0",
        "status": "ready_validation_plan_vmv_deferred",
        "created_at": created_at,
        "input_paths": {
            "multiview_summary": rel_path(args.multiview_summary),
            "codex_smoke_summary": rel_path(args.codex_smoke_summary),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "reference_codex_smoke_metrics": baseline_metrics(codex),
        "available_audit_candidates": multiview.get("counts", {}),
        "target_requirements": TARGET_REQUIREMENTS,
        "control_plan": CONTROL_PLAN,
        "acceptance_rule": ACCEPTANCE_RULE,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "paper_result": False,
            "vmv_model_input_allowed": False,
            "posterior_claim_allowed": False,
        },
        "next_gate": "36_controlled_label_target.md",
    }
    write_json(paths["protocol"], protocol)
    write_json(paths["summary"], summary)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    req = summary["target_requirements"]["hypothesis_stage_minimum"]
    print(
        f"status={summary['status']} "
        f"hypothesis_rows_min={req['usable_binary_rows_min']} "
        f"per_class_min={req['per_class_min']} "
        f"vmv_input={summary['boundary']['vmv_model_input_allowed']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
