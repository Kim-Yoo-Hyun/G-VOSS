#!/usr/bin/env python3
"""Synthesize the support/contact generalization repair protocol for H002."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def fval(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, "")
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def find_row(rows: list[dict[str, str]], **conds: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(k) == v for k, v in conds.items()):
            return row
    return {}


def label_value(row: dict[str, Any]) -> int:
    labels = row.get("labels", {})
    value = labels.get("C_e", labels.get("target_y", 0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def get_feature_vector(row: dict[str, Any]) -> dict[str, float]:
    g = row.get("feature_blocks", {}).get("G_e", {})
    vec = g.get("g_e_feature_vector", {})
    out: dict[str, float] = {}
    for key, value in vec.items():
        try:
            out[key] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def summarize_features(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values_by_label: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    availability: Counter[str] = Counter()
    feature_names: set[str] = set()

    for row in rows:
        y = label_value(row)
        g = row.get("feature_blocks", {}).get("G_e", {})
        mask = g.get("g_e_feature_mask", {})
        vec = get_feature_vector(row)
        feature_names.update(vec)
        for name, available in mask.items():
            if available:
                availability[name] += 1
        for name, value in vec.items():
            values_by_label[name][y].append(value)

    out: list[dict[str, Any]] = []
    row_count = max(len(rows), 1)
    for name in sorted(feature_names):
        pos_values = values_by_label[name].get(1, [])
        neg_values = values_by_label[name].get(0, [])
        pos_mean = mean(pos_values) if pos_values else 0.0
        neg_mean = mean(neg_values) if neg_values else 0.0
        out.append(
            {
                "feature": name,
                "available_rows": availability.get(name, 0),
                "availability_rate": availability.get(name, 0) / row_count,
                "mean_label_1": pos_mean,
                "mean_label_0": neg_mean,
                "diff_pos_minus_neg": pos_mean - neg_mean,
                "repair_interpretation": feature_interpretation(name),
            }
        )
    return out


def feature_interpretation(name: str) -> str:
    if "gap" in name or "contact" in name or "surface" in name:
        return "contact_surface_signal"
    if "axis" in name or "flatness" in name or "extent" in name or "upness" in name:
        return "pose_orientation_signal"
    if "overlap" in name or "xy" in name:
        return "support_footprint_signal"
    if "point" in name or "density" in name:
        return "point_evidence_signal"
    return "generic_geometry_signal"


def summarize_failures(failure_rows: list[dict[str, Any]], hidden_by_id: dict[str, dict[str, Any]]) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]]
]:
    by_pred: dict[str, Counter[str]] = defaultdict(Counter)
    by_pair: dict[str, Counter[str]] = defaultdict(Counter)

    for row in failure_rows:
        predicate = row.get("predicate_label", "")
        pair = row.get("class_pair", "")
        if not pair:
            hidden = hidden_by_id.get(row.get("candidate_id", ""), {})
            pair = hidden.get("class_pair", "")
        target = int(row.get("target_y", 0))
        predicted = int(row.get("predicted", 0))
        err_type = "FP" if target == 0 and predicted == 1 else "FN" if target == 1 and predicted == 0 else "OTHER"
        by_pred[predicate][err_type] += 1
        by_pred[predicate]["total"] += 1
        by_pair[pair][err_type] += 1
        by_pair[pair]["total"] += 1

    pred_rows: list[dict[str, Any]] = []
    for predicate, cnt in sorted(by_pred.items()):
        pred_rows.append(
            {
                "predicate_label": predicate,
                "failure_rows": cnt["total"],
                "false_positive": cnt["FP"],
                "false_negative": cnt["FN"],
                "dominant_error": "false_positive" if cnt["FP"] >= cnt["FN"] else "false_negative",
                "repair_implication": (
                    "needs_lying_pose_evidence"
                    if predicate == "lying on"
                    else "needs_upright_support_pose_evidence"
                    if predicate == "standing on"
                    else "needs_predicate_specific_support_subtype"
                ),
            }
        )

    pair_rows: list[dict[str, Any]] = []
    sorted_pairs = sorted(by_pair.items(), key=lambda item: (-item[1]["total"], item[0]))
    for pair, cnt in sorted_pairs[:20]:
        pair_rows.append(
            {
                "class_pair": pair,
                "failure_rows": cnt["total"],
                "lying_on_false_positive": cnt["FP"] if pair else cnt["FP"],
                "standing_on_false_negative": cnt["FN"] if pair else cnt["FN"],
                "repair_implication": "class_pair_pose_prior_or_counterfactual_label_ambiguity",
            }
        )

    return pred_rows, pair_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    materialization_dir = root / "experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"
    evaluation_dir = root / "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest"
    official_eval_dir = root / "experiments/H002_compatibility_routing/official_evaluation/latest"
    general_gap_dir = root / "experiments/H002_compatibility_routing/general_framework_gap/latest"

    row_manifest = read_json(materialization_dir / "row_manifest.json")
    eval_manifest = read_json(evaluation_dir / "eval_manifest.json")
    general_gap = read_json(general_gap_dir / "summary.json")
    model_rows = read_jsonl(materialization_dir / "model_safe_main_no_class.jsonl")
    hidden_rows = read_jsonl(materialization_dir / "hidden_manifest.jsonl")
    failure_rows = read_jsonl(evaluation_dir / "failure_rows.jsonl")
    official_metrics = read_csv(evaluation_dir / "official_metrics.csv")
    dev_metrics = read_csv(evaluation_dir / "dev_metrics.csv")
    official_family = read_csv(official_eval_dir / "family_metrics.csv")

    validation_errors: list[dict[str, Any]] = []
    required_paths = [
        materialization_dir / "row_manifest.json",
        materialization_dir / "model_safe_main_no_class.jsonl",
        materialization_dir / "hidden_manifest.jsonl",
        evaluation_dir / "official_metrics.csv",
        evaluation_dir / "dev_metrics.csv",
        evaluation_dir / "failure_rows.jsonl",
    ]
    for path in required_paths:
        if not path.exists():
            validation_errors.append({"type": "missing_required_path", "path": str(path)})

    hidden_by_id = {row.get("candidate_id", ""): row for row in hidden_rows}
    label_counts = Counter(label_value(row) for row in model_rows)
    predicate_counts = Counter(row.get("predicate_label", "") for row in model_rows)
    feature_rows = summarize_features(model_rows)
    feature_count = len(feature_rows)
    fully_available_features = sum(1 for row in feature_rows if float(row["availability_rate"]) == 1.0)

    pred_failure_rows, class_pair_failure_rows = summarize_failures(failure_rows, hidden_by_id)

    official_m4 = find_row(official_metrics, view_id="M4_TxG_compatibility", level="overall")
    official_m2 = find_row(official_metrics, view_id="M2_geometry_only", level="overall")
    official_m3 = find_row(official_metrics, view_id="M3_T_plus_G_concat", level="overall")
    dev_m4 = find_row(dev_metrics, view_id="M4_TxG_compatibility", level="overall")
    broad_m4 = find_row(
        official_family,
        route_family="support_contact",
        predicate_label="ALL",
        view_id="M4_TxG_compatibility",
    )

    current_hard_official_pass = (
        fval(official_m4, "auroc") >= 0.70
        and fval(official_m4, "auroc") > fval(official_m2, "auroc")
        and fval(official_m4, "auroc") > fval(official_m3, "auroc")
    )

    taxonomy_rows = [
        {
            "failure_mode": "pose_subtype_target_ambiguity",
            "evidence": "high-confidence errors are paired as lying-on false positives and standing-on false negatives",
            "root_cause": "the same support pair is forced into predicate-flip labels without independent pose observability",
            "repair_action": "split standing_on and lying_on into pose-aware subtype targets; add ambiguous_support abstain state",
            "paper_claim_impact": "blocks support/contact solved claim until repaired",
        },
        {
            "failure_mode": "feature_coverage_not_primary_bottleneck",
            "evidence": f"{fully_available_features}/{feature_count} current G_e features are available on all rows",
            "root_cause": "features exist, but target semantics and predicate-specific pose evidence are insufficient",
            "repair_action": "change target and route protocol before adding more model capacity",
            "paper_claim_impact": "supports principled repair rather than post-hoc model tuning",
        },
        {
            "failure_mode": "official_generalization_inversion",
            "evidence": (
                f"internal dev M4 AUROC={fval(dev_m4, 'auroc'):.6f}; "
                f"official hard-route M4 AUROC={fval(official_m4, 'auroc'):.6f}"
            ),
            "root_cause": "internal counterfactual signal does not transfer to official validation label distribution",
            "repair_action": "freeze official-validation eval-only protocol and rebuild train/dev support/contact targets with matched class-pair/pose strata",
            "paper_claim_impact": "current support/contact is failure taxonomy, not solved evidence",
        },
        {
            "failure_mode": "class_pair_pose_prior_concentration",
            "evidence": "top high-confidence failures concentrate in sofa/couch/table/cabinet/shelf to floor pairs",
            "root_cause": "object-class prior and floor-support semantics entangle with true pose state",
            "repair_action": "class-pair balanced materialization with within-class-pair accept/reject/abstain strata",
            "paper_claim_impact": "prevents class-pair shortcut from masquerading as compatibility",
        },
        {
            "failure_mode": "superordinate_support_boundary",
            "evidence": "supported by is broader than standing_on/lying_on and can be true when subtype is uncertain",
            "root_cause": "binary subtype labels collapse support existence, pose subtype, and observability",
            "repair_action": "treat supported_by as relabel/decomposition/abstain diagnostic, not direct binary C_e target",
            "paper_claim_impact": "keeps H002 route-aware rather than forcing all support labels into one classifier",
        },
    ]

    protocol_rows = [
        {
            "step": "R1",
            "scope": "standing on",
            "action": "define upright-support subtype target",
            "input_view": "G_e without predicate/source score; hidden visual/mesh audit for label only",
            "output_artifact": "standing_on_pose_safe_rows.jsonl",
            "gate": "accept/reject/abstain labels balanced within class-pair strata",
        },
        {
            "step": "R2",
            "scope": "lying on",
            "action": "define horizontal-support subtype target",
            "input_view": "G_e pose/orientation/contact features; visual/mesh audit for label only",
            "output_artifact": "lying_on_pose_safe_rows.jsonl",
            "gate": "lying pose evidence must not be inferred only from class pair",
        },
        {
            "step": "R3",
            "scope": "supported by",
            "action": "route to superordinate support decomposition",
            "input_view": "support existence evidence plus subtype uncertainty",
            "output_artifact": "supported_by_relabel_abstain_rows.jsonl",
            "gate": "no direct binary solved claim; report relabel/abstain diagnostic",
        },
        {
            "step": "R4",
            "scope": "Q_e",
            "action": "separate pose observability from geometry compatibility",
            "input_view": "mesh completeness, point density, multi-view confirmation, occlusion flags",
            "output_artifact": "support_contact_qe_pose_observability.jsonl",
            "gate": "Q_e not allowed inside C_e main compatibility input",
        },
        {
            "step": "R5",
            "scope": "controls",
            "action": "add pose-aware controls",
            "input_view": "wrong predicate, shuffled G_e, within-class-pair shuffled G_e, subject/object swap",
            "output_artifact": "support_contact_repair_controls.csv",
            "gate": "T_x_G improves over T-only/G-only/concat and controls collapse",
        },
    ]

    gate_rows = [
        {
            "gate": "schema_separation",
            "pass_condition": "model-safe view excludes Z_e, class labels, target construction fields, GT flags, and Q_e from C_e",
            "current_state": "previous materialization passed; must recheck after repair",
            "decision": "required",
            "next_needed": "run schema audit on repaired rows",
        },
        {
            "gate": "feature_coverage",
            "pass_condition": "canonical G_e features available or explicitly masked; no hidden label-derived feature",
            "current_state": f"{fully_available_features}/{feature_count} current features available on all rows",
            "decision": "coverage_ok_but_not_sufficient",
            "next_needed": "add pose/visual audit labels, not just more numeric G_e",
        },
        {
            "gate": "support_contact_metric",
            "pass_condition": "official validation M4 AUROC >= 0.70 and > T-only/G-only/concat",
            "current_state": f"official hard-route M4 AUROC={fval(official_m4, 'auroc'):.6f}",
            "decision": "failed",
            "next_needed": "repair subtype labels and rematerialize before re-running metric",
        },
        {
            "gate": "control_collapse",
            "pass_condition": "wrong-T and shuffled-G controls degrade below primary M4",
            "current_state": "previous wrong-T outperformed M4, indicating inversion",
            "decision": "failed",
            "next_needed": "rebuild controls after pose-aware target repair",
        },
        {
            "gate": "class_pair_control",
            "pass_condition": "within class-pair accept/reject/abstain strata exist for top support pairs",
            "current_state": "high-confidence failures concentrate in floor support class pairs",
            "decision": "required",
            "next_needed": "cap and balance class-pair strata",
        },
        {
            "gate": "paper_claim",
            "pass_condition": "support/contact can be described as solved compatibility route",
            "current_state": "not solved",
            "decision": "blocked",
            "next_needed": "keep as diagnostic until repaired metrics pass",
        },
    ]

    write_csv(
        out / "feature_gap.csv",
        feature_rows,
        [
            "feature",
            "available_rows",
            "availability_rate",
            "mean_label_1",
            "mean_label_0",
            "diff_pos_minus_neg",
            "repair_interpretation",
        ],
    )
    write_csv(
        out / "predicate_error_summary.csv",
        pred_failure_rows,
        ["predicate_label", "failure_rows", "false_positive", "false_negative", "dominant_error", "repair_implication"],
    )
    write_csv(
        out / "class_pair_error_summary.csv",
        class_pair_failure_rows,
        ["class_pair", "failure_rows", "lying_on_false_positive", "standing_on_false_negative", "repair_implication"],
    )
    write_csv(
        out / "failure_taxonomy.csv",
        taxonomy_rows,
        ["failure_mode", "evidence", "root_cause", "repair_action", "paper_claim_impact"],
    )
    write_csv(
        out / "repair_protocol.csv",
        protocol_rows,
        ["step", "scope", "action", "input_view", "output_artifact", "gate"],
    )
    write_csv(
        out / "gate_plan.csv",
        gate_rows,
        ["gate", "pass_condition", "current_state", "decision", "next_needed"],
    )

    with (out / "validation_errors.jsonl").open("w", encoding="utf-8") as f:
        for err in validation_errors:
            f.write(json.dumps(err, sort_keys=True) + "\n")

    summary = {
        "status": "h002_support_contact_generalization_repair_ready",
        "schema_version": "h002_support_contact_generalization_repair_v1",
        "validation_errors": len(validation_errors),
        "source_artifacts": {
            "materialization": str(materialization_dir.relative_to(root)),
            "evaluation": str(evaluation_dir.relative_to(root)),
            "general_framework_gap": str(general_gap_dir.relative_to(root)),
        },
        "source_status": {
            "row_manifest_status": row_manifest.get("status", ""),
            "eval_manifest_status": eval_manifest.get("status", ""),
            "general_framework_claim": general_gap.get("decisions", {}).get("general_framework_claim", ""),
        },
        "counts": {
            "candidate_rows": len(model_rows),
            "hidden_rows": len(hidden_rows),
            "failure_rows": len(failure_rows),
            "label_counts": dict(label_counts),
            "predicate_counts": dict(predicate_counts),
            "feature_count": feature_count,
            "fully_available_feature_count": fully_available_features,
        },
        "metrics": {
            "hard_official_M4_AUROC": fval(official_m4, "auroc"),
            "hard_official_M4_balanced_accuracy": fval(official_m4, "balanced_accuracy"),
            "hard_official_G_only_AUROC": fval(official_m2, "auroc"),
            "hard_official_concat_AUROC": fval(official_m3, "auroc"),
            "hard_internal_dev_M4_AUROC": fval(dev_m4, "auroc"),
            "broad_official_support_contact_M4_AUROC": fval(broad_m4, "auroc"),
            "current_hard_official_pass": current_hard_official_pass,
        },
        "decision": {
            "support_contact_solved": False,
            "selected_path": "pose_aware_relabel_abstain_repair_before_more_model_capacity",
            "support_contact_paper_role": "diagnostic_failure_taxonomy_until_repaired_metric_passes",
            "reason": "current G_e coverage is complete but hard official route inverts; target semantics and pose observability must be repaired",
            "next_todo": "support_contact_generalization_repair_materialization",
        },
    }
    write_json(out / "summary.json", summary)
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
