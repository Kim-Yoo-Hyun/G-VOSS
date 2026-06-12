#!/usr/bin/env python3
"""Write the H002 train-only factorized reliability contract."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_WORKING_LABELS = RGA_ROOT / "manual_audit/working_labels.jsonl"
DEFAULT_RGA_SUMMARY = RGA_ROOT / "train_rga_summary.json"
DEFAULT_MANUAL_SUMMARY = RGA_ROOT / "manual_audit/train_manual_audit_summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "factor_contract"


STRICT_POSITIVE = {"true_underconfidence"}
STRICT_NEGATIVE = {"semantic_overconfidence"}
WEAK_POSITIVE = {"true_underconfidence", "annotation_sparsity"}
WEAK_NEGATIVE = {"semantic_overconfidence", "dense_relation_noise"}
REPAIR_CANDIDATE = {"ontology_mismatch"}
ABSTAIN = {"uncertain_needs_visual_or_mesh", "object_pair_error", "geometry_artifact"}

SOFT_TARGET = {
    "true_underconfidence": 1.0,
    "annotation_sparsity": 0.7,
    "ontology_mismatch": 0.5,
    "semantic_overconfidence": 0.0,
    "dense_relation_noise": 0.2,
    "object_pair_error": 0.0,
    "geometry_artifact": 0.0,
    "uncertain_needs_visual_or_mesh": None,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-labels", type=Path, default=DEFAULT_WORKING_LABELS)
    parser.add_argument("--rga-summary", type=Path, default=DEFAULT_RGA_SUMMARY)
    parser.add_argument("--manual-summary", type=Path, default=DEFAULT_MANUAL_SUMMARY)
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
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def strict_target(label: str) -> int | None:
    if label in STRICT_POSITIVE:
        return 1
    if label in STRICT_NEGATIVE:
        return 0
    return None


def weak_target(label: str) -> int | None:
    if label in WEAK_POSITIVE:
        return 1
    if label in WEAK_NEGATIVE:
        return 0
    return None


def action_target(label: str) -> str:
    if label == "true_underconfidence":
        return "promote_or_keep_candidate"
    if label == "annotation_sparsity":
        return "audit_annotation_or_keep_weak"
    if label == "ontology_mismatch":
        return "predicate_relabel_or_multi_relation_review"
    if label == "semantic_overconfidence":
        return "reject_or_downweight"
    if label == "dense_relation_noise":
        return "do_not_promote_dense_relation"
    if label in {"object_pair_error", "geometry_artifact"}:
        return "reject_after_evidence_check"
    return "abstain_needs_human_review"


def sample_weight(label: str, confidence: str) -> float:
    if label == "true_underconfidence":
        return 1.0
    if label == "semantic_overconfidence":
        return 1.0
    if label in {"annotation_sparsity", "dense_relation_noise"}:
        return 0.5
    if label == "ontology_mismatch":
        return 0.25
    if confidence == "medium":
        return 0.25
    return 0.0


def factor_target_row(row: dict[str, Any]) -> dict[str, Any]:
    working = row.get("working_audit") or {}
    label = str(working.get("working_label"))
    confidence = str(working.get("working_label_confidence"))
    return {
        "schema_version": "h002_factor_target_v0",
        "audit_id": row.get("audit_id"),
        "prediction_id": row.get("prediction_id"),
        "queue_kind": row.get("queue_kind"),
        "predicate_family": row.get("predicate_family"),
        "predicate_label": row.get("predicate_label"),
        "label_match_status": row.get("label_match_status"),
        "geometry_status": row.get("geometry_status"),
        "h001_verification_status": row.get("h001_verification_status"),
        "semantic_rank": row.get("semantic_rank"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "p_geom_valid": row.get("p_geom_valid"),
        "working_label": label,
        "working_label_confidence": confidence,
        "strict_binary_target": strict_target(label),
        "weak_binary_target": weak_target(label),
        "soft_reliability_target": SOFT_TARGET.get(label),
        "action_target": action_target(label),
        "sample_weight": sample_weight(label, confidence),
        "target_source": "machine_assisted_working_label",
        "paper_locked": False,
        "human_confirmed": False,
        "leakage_boundary": (
            "Target labels may supervise train-only hypothesis-stage fitting. "
            "They are not deployment-time input features."
        ),
    }


def feature_blocks() -> dict[str, Any]:
    return {
        "schema_version": "h002_feature_blocks_v0",
        "semantic_evidence": {
            "prefix": "S_e",
            "features": [
                "semantic_score_raw",
                "semantic_score_norm",
                "rank_in_context",
                "predicate_rank_for_pair",
                "top50_semantic",
                "top100_semantic",
                "predicate_label",
                "predicate_family",
                "source_id",
            ],
            "deployment_allowed": True,
        },
        "geometry_evidence": {
            "prefix": "G_e",
            "features": [
                "geometry_status",
                "p_geom_valid",
                "p_geom_invalid",
                "consistency_score",
                "geometry_residual_proxy",
                "reason_codes",
                "raw_features",
                "selected_policy",
            ],
            "deployment_allowed": True,
        },
        "coverage_evidence": {
            "prefix": "C_e",
            "features": [
                "coverage_state",
                "geometry_available",
                "geometry_checkable",
                "predicate_family_supported",
                "missing_geometry",
                "unsupported_family",
                "visual_asset_available_for_audit",
            ],
            "deployment_allowed": True,
        },
        "uncertainty_evidence": {
            "prefix": "U_e",
            "features": [
                "geometry_status_is_uncertain",
                "semantic_geometry_disagreement_score",
                "underconfidence_score",
                "absolute_disagreement",
                "low_working_label_confidence_if_available",
                "abstain_reason_codes",
            ],
            "deployment_allowed": True,
        },
        "label_or_audit_evidence": {
            "prefix": "L_e",
            "features": [
                "exact_match",
                "family_match",
                "pair_has_other_predicate",
                "no_gt_for_pair",
                "working_label",
                "human_final_audit_label",
            ],
            "deployment_allowed": False,
            "allowed_use": [
                "train_supervision",
                "calibration_target",
                "evaluation_stratification",
                "oracle_diagnostic_only",
            ],
        },
        "interactions": {
            "prefix": "I_e",
            "features": [
                "semantic_score_norm_minus_p_geom_valid",
                "top100_and_unsatisfied",
                "tail_gt100_and_satisfied",
                "covered_and_uncertain",
                "family_specific_semantic_geometry_terms",
            ],
            "deployment_allowed": True,
        },
    }


def baseline_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_baseline_contract_v0",
        "baselines": [
            {
                "name": "semantic_only",
                "score": "calibrated semantic rank/score",
                "feature_blocks": ["semantic_evidence"],
                "deployment_allowed": True,
                "role": "tests whether source confidence alone explains relation reliability",
            },
            {
                "name": "geometry_only",
                "score": "p_geom_valid plus geometry status as optional ablation",
                "feature_blocks": ["geometry_evidence", "coverage_evidence"],
                "deployment_allowed": True,
                "role": "tests whether calibrated geometry validity alone explains reliability",
            },
            {
                "name": "semantic_plus_geometry",
                "score": "semantic_score_norm * p_geom_valid or two-factor logistic model",
                "feature_blocks": ["semantic_evidence", "geometry_evidence"],
                "deployment_allowed": True,
                "role": "H001-style fusion baseline",
            },
            {
                "name": "factorized_reliability_posterior",
                "score": "P(R_e=1 | S_e, G_e, C_e, U_e), trained with L_e as supervision not input",
                "feature_blocks": [
                    "semantic_evidence",
                    "geometry_evidence",
                    "coverage_evidence",
                    "uncertainty_evidence",
                    "interactions",
                ],
                "deployment_allowed": True,
                "role": "H002 proposed deployable posterior",
            },
            {
                "name": "oracle_label_factor_diagnostic",
                "score": "P(R_e=1 | S_e, L_e, G_e, C_e, U_e)",
                "feature_blocks": [
                    "semantic_evidence",
                    "label_or_audit_evidence",
                    "geometry_evidence",
                    "coverage_evidence",
                    "uncertainty_evidence",
                    "interactions",
                ],
                "deployment_allowed": False,
                "role": "diagnostic upper-bound only; not a deployable baseline",
            },
        ],
        "minimum_main_table_conditions": [
            "semantic_only",
            "geometry_only",
            "semantic_plus_geometry",
            "factorized_reliability_posterior",
        ],
        "oracle_not_main_comparison": "oracle_label_factor_diagnostic",
    }


def target_contract() -> dict[str, Any]:
    all_labels = (
        STRICT_POSITIVE
        | STRICT_NEGATIVE
        | WEAK_POSITIVE
        | WEAK_NEGATIVE
        | REPAIR_CANDIDATE
        | ABSTAIN
    )
    return {
        "schema_version": "h002_target_contract_v0",
        "latent_variable": "R_e",
        "definition": "edge is reliable enough to keep, use, or promote under current task policy",
        "strict_binary_target": {
            "positive": sorted(STRICT_POSITIVE),
            "negative": sorted(STRICT_NEGATIVE),
            "exclude": sorted(all_labels - STRICT_POSITIVE - STRICT_NEGATIVE),
            "use": "clean train-only smoke target; small but least ambiguous",
        },
        "weak_binary_target": {
            "positive": sorted(WEAK_POSITIVE),
            "negative": sorted(WEAK_NEGATIVE),
            "exclude": sorted(all_labels - WEAK_POSITIVE - WEAK_NEGATIVE),
            "use": "hypothesis-stage weak supervision only",
        },
        "soft_target": {
            "mapping": SOFT_TARGET,
            "use": "sensitivity analysis only; not paper-final unless human-confirmed",
        },
        "action_target": {
            "classes": [
                "promote_or_keep_candidate",
                "audit_annotation_or_keep_weak",
                "predicate_relabel_or_multi_relation_review",
                "reject_or_downweight",
                "do_not_promote_dense_relation",
                "reject_after_evidence_check",
                "abstain_needs_human_review",
            ],
            "use": "graph repair/action framing after reliability posterior is validated",
        },
        "label_source_boundary": (
            "Current targets come from machine-assisted working labels. They are acceptable for "
            "train-only hypothesis-stage smoke tests, not for paper-locked claims."
        ),
    }


def summarize_targets(rows: list[dict[str, Any]], targets: list[dict[str, Any]]) -> dict[str, Any]:
    working = Counter(target["working_label"] for target in targets)
    strict = Counter("positive" if t["strict_binary_target"] == 1 else "negative" if t["strict_binary_target"] == 0 else "excluded" for t in targets)
    weak = Counter("positive" if t["weak_binary_target"] == 1 else "negative" if t["weak_binary_target"] == 0 else "excluded" for t in targets)
    action = Counter(t["action_target"] for t in targets)
    by_family_working = Counter((t["predicate_family"], t["working_label"]) for t in targets)
    by_queue_working = Counter((t["queue_kind"], t["working_label"]) for t in targets)
    weight_sum = sum(float(t["sample_weight"]) for t in targets)
    return {
        "rows": len(rows),
        "working_label": dict(sorted(working.items())),
        "strict_binary": dict(sorted(strict.items())),
        "weak_binary": dict(sorted(weak.items())),
        "action_target": dict(sorted(action.items())),
        "family_working_label": {
            f"{family}|{label}": count
            for (family, label), count in sorted(by_family_working.items())
        },
        "queue_working_label": {
            f"{queue}|{label}": count
            for (queue, label), count in sorted(by_queue_working.items())
        },
        "sample_weight_sum": weight_sum,
        "strict_usable_rows": strict["positive"] + strict["negative"],
        "weak_usable_rows": weak["positive"] + weak["negative"],
        "strict_positive_rate": safe_rate(strict["positive"], strict["positive"] + strict["negative"]),
        "weak_positive_rate": safe_rate(weak["positive"], weak["positive"] + weak["negative"]),
    }


def make_contract(
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    rga_summary: dict[str, Any],
    manual_summary: dict[str, Any],
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "h002_factor_contract_v0",
        "status": "ready",
        "created_at": created_at,
        "input_paths": {
            "working_labels": rel_path(args.working_labels),
            "rga_summary": rel_path(args.rga_summary),
            "manual_summary": rel_path(args.manual_summary),
        },
        "output_paths": {
            "factor_contract": rel_path(as_abs(args.output_dir) / "factor_contract.json"),
            "feature_blocks": rel_path(as_abs(args.output_dir) / "feature_blocks.json"),
            "baseline_contract": rel_path(as_abs(args.output_dir) / "baseline_contract.json"),
            "factor_targets": rel_path(as_abs(args.output_dir) / "factor_targets.jsonl"),
            "report": rel_path(as_abs(args.output_dir) / "report.md"),
        },
        "problem": {
            "posterior": "P(R_e=1 | S_e, G_e, C_e, U_e)",
            "oracle_diagnostic": "P(R_e=1 | S_e, L_e, G_e, C_e, U_e)",
            "factor_form": (
                "P(R_e=1 | S_e,G_e,C_e,U_e) ∝ "
                "psi_sem(R_e,S_e) psi_geom(R_e,G_e) psi_cov(R_e,C_e) "
                "psi_unc(R_e,U_e) psi_interact(R_e,S_e,G_e,C_e)"
            ),
            "label_factor_boundary": (
                "L_e is supervision/evaluation/oracle-diagnostic evidence, not a deployable input."
            ),
        },
        "source_counts": {
            "manual_audit_rows": manual_summary["counts"]["rows"],
            "human_confirmed_share": manual_summary["rates"]["human_confirmed_share"],
            "rga_prediction_rows": rga_summary["input_counts"]["prediction_rows"],
            "rga_top100_hl": rga_summary["metrics_by_k"]["100"]["high_semantic"]["top100_unsatisfied"],
            "rga_tail100_lh": rga_summary["metrics_by_k"]["100"]["low_semantic_tail"]["tail_gt100_satisfied"],
        },
        "target_contract": target_contract(),
        "feature_blocks": feature_blocks(),
        "baseline_contract": baseline_contract(),
        "target_summary": summarize_targets(rows, targets),
        "leakage_rules": {
            "validation_usage": "forbidden for H002 hypothesis-stage target/threshold/model selection",
            "label_match_as_input": "forbidden in deployable posterior",
            "working_label_as_input": "forbidden in deployable posterior",
            "human_label_as_input": "forbidden in deployable posterior unless evaluating an oracle diagnostic",
            "allowed_label_usage": [
                "training target",
                "calibration target",
                "evaluation stratification",
                "oracle diagnostic upper bound",
            ],
        },
        "next_gate": {
            "document": "26_factor_dataset.md",
            "goal": (
                "materialize deployable feature rows and strict/weak target rows for "
                "train-only smoke fitting without validation leakage"
            ),
        },
    }


def write_report(path: Path, contract: dict[str, Any]) -> None:
    target = contract["target_summary"]
    baselines = contract["baseline_contract"]["baselines"]
    lines = [
        "# H002 Factor Contract",
        "",
        f"Created at: `{contract['created_at']}`",
        "",
        "## Posterior",
        "",
        "Deployable posterior:",
        "",
        "```text",
        contract["problem"]["posterior"],
        "```",
        "",
        "Oracle diagnostic only:",
        "",
        "```text",
        contract["problem"]["oracle_diagnostic"],
        "```",
        "",
        "## Target Counts",
        "",
        "| Target | Positive | Negative | Excluded | Usable |",
        "| --- | ---: | ---: | ---: | ---: |",
        (
            f"| strict | {target['strict_binary'].get('positive', 0)} | "
            f"{target['strict_binary'].get('negative', 0)} | "
            f"{target['strict_binary'].get('excluded', 0)} | {target['strict_usable_rows']} |"
        ),
        (
            f"| weak | {target['weak_binary'].get('positive', 0)} | "
            f"{target['weak_binary'].get('negative', 0)} | "
            f"{target['weak_binary'].get('excluded', 0)} | {target['weak_usable_rows']} |"
        ),
        "",
        "## Baselines",
        "",
        "| Baseline | Deployment | Feature blocks |",
        "| --- | --- | --- |",
    ]
    for baseline in baselines:
        lines.append(
            f"| `{baseline['name']}` | `{str(baseline['deployment_allowed']).lower()}` | "
            f"`{', '.join(baseline['feature_blocks'])}` |"
        )

    lines.extend(
        [
            "",
            "## Leakage Rules",
            "",
            "- Label match and working labels are targets/evaluation strata, not deployable input features.",
            "- `oracle_label_factor_diagnostic` is not a main-table deployable baseline.",
            "- Validation artifacts remain forbidden for H002 hypothesis-stage selection.",
            "",
            "## Next Gate",
            "",
            "`26_factor_dataset.md`: materialize train-only feature rows and target rows for smoke fitting.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(args.working_labels)
    targets = [factor_target_row(row) for row in rows]
    rga_summary = read_json(args.rga_summary)
    manual_summary = read_json(args.manual_summary)
    contract = make_contract(args, rows, targets, rga_summary, manual_summary)

    write_json(output_dir / "factor_contract.json", contract)
    write_json(output_dir / "feature_blocks.json", contract["feature_blocks"])
    write_json(output_dir / "baseline_contract.json", contract["baseline_contract"])
    write_jsonl(output_dir / "factor_targets.jsonl", targets)
    write_report(output_dir / "report.md", contract)

    print(
        f"status={contract['status']} rows={contract['target_summary']['rows']} "
        f"strict={contract['target_summary']['strict_usable_rows']} "
        f"weak={contract['target_summary']['weak_usable_rows']} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
