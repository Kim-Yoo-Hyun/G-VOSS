#!/usr/bin/env python3
"""Write the H002 compatibility-learning scope plan after attachment target freeze."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PATH_DECISION = H2_ROOT / "artifacts/attachment_independent_positive_anchor_path_decision_after_audit_v1"
DEFAULT_PROTOTYPE = H2_ROOT / "artifacts/prototype_dataset_v1"
DEFAULT_SMOKE = H2_ROOT / "artifacts/smoke_baseline_v1"
DEFAULT_LEARNED = H2_ROOT / "artifacts/learned_smoke_v1"
DEFAULT_ATTACHMENT_SMOKE = H2_ROOT / "artifacts/attachment_numeric_geometry_smoke_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_learning_scope_plan_v1"

EXPECTED_PATH_STATUS = "h002_attachment_independent_positive_anchor_path_decision_diagnostic_freeze"
EXPECTED_PATH_NEXT = "compatibility_learning_scope_plan_v1"

SCHEMA_VERSION = "h002_compatibility_learning_scope_plan_v1"
STATUS_READY = "h002_compatibility_learning_scope_plan_ready"
STATUS_ERRORS = "h002_compatibility_learning_scope_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v2_contract"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--prototype-dir", type=Path, default=DEFAULT_PROTOTYPE)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE)
    parser.add_argument("--learned-dir", type=Path, default=DEFAULT_LEARNED)
    parser.add_argument("--attachment-smoke-dir", type=Path, default=DEFAULT_ATTACHMENT_SMOKE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    path_decision: dict[str, Any],
    prototype: dict[str, Any],
    smoke: dict[str, Any],
    learned: dict[str, Any],
    attachment_smoke: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_next", "actual": path_decision.get("next_todo")})
    if path_decision.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "path_decision_allows_posterior", "actual": path_decision.get("posterior_smoke_allowed")})
    if path_decision.get("validation_errors") != 0:
        errors.append({"error_type": "path_decision_validation_errors", "actual": path_decision.get("validation_errors")})

    expected_status = {
        "prototype": (prototype, "h002_prototype_dataset_v1_ready"),
        "smoke": (smoke, "h002_smoke_baseline_v1_completed"),
        "learned": (learned, "h002_learned_smoke_v1_completed"),
        "attachment_smoke": (attachment_smoke, "h002_attachment_numeric_geometry_smoke_v1_completed"),
    }
    for name, (payload, status) in expected_status.items():
        if payload.get("status") != status:
            errors.append({"error_type": "unexpected_input_status", "input": name, "expected": status, "actual": payload.get("status")})
        if payload.get("counts", {}).get("validation_errors") not in (0, None):
            errors.append(
                {
                    "error_type": "input_count_validation_errors",
                    "input": name,
                    "actual": payload.get("counts", {}).get("validation_errors"),
                }
            )
        if payload.get("validation_errors") not in (0, None):
            errors.append({"error_type": "input_validation_errors", "input": name, "actual": payload.get("validation_errors")})

    for name, payload in [
        ("smoke", smoke),
        ("learned", learned),
        ("attachment_smoke", attachment_smoke),
    ]:
        boundary = payload.get("boundary", {})
        for key in ("validation_usage", "test_usage", "paper_evidence_allowed"):
            if boundary.get(key) is not False:
                errors.append({"error_type": "boundary_not_false", "input": name, "key": key, "actual": boundary.get(key)})
    return errors


def row_family_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family = Counter()
    task_a = Counter()
    predicates: dict[str, Counter[str]] = {}
    for row in rows:
        family = row.get("T_e", {}).get("relation_family", "unknown")
        by_family[family] += 1
        predicates.setdefault(family, Counter())[row.get("T_e", {}).get("predicate_label", "unknown")] += 1
        label = row.get("counterfactual_axis", {}).get("compatibility_label")
        if label in {"positive", "counterfactual_negative"}:
            task_a[(family, label)] += 1
    return {
        "rows_by_family": dict(sorted(by_family.items())),
        "compatibility_by_family": {f"{family}|{label}": count for (family, label), count in sorted(task_a.items())},
        "predicates_by_family": {family: dict(sorted(counts.items())) for family, counts in sorted(predicates.items())},
    }


def family_scope_rows(prototype: dict[str, Any], learned: dict[str, Any], attachment_smoke: dict[str, Any], path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    learned_gates = learned.get("gates", {})
    attach_gates = attachment_smoke.get("gates", {})
    return [
        {
            "relation_family": "support_contact",
            "predicates": "standing on; lying on; supported by",
            "scope_status": "primary_v1",
            "main_use": "C_e compatibility learning and source/geometry/factorized smoke",
            "positive_tiers": "P1 audit/user-confirmed; P2 high-precision geometry-verified; optional P0 GT+geometry-usable",
            "negative_tiers": "N1 wrong-pair; N2 shuffled geometry; N5 contact/support perturbation; N6 same-family/rank/coverage hard negative",
            "allowed_g_e": "raw witness v2 numeric pair geometry; contact gap; XY overlap; support overlap; vertical gap; p_geom_valid only as baseline/teacher",
            "allowed_q_e": "raw witness availability; geometry coverage; missing/artifact flags",
            "current_evidence": (
                f"prototype rows {prototype.get('counts', {}).get('by_family', {}).get('support_contact')}; "
                f"learned T+G AUROC {learned_gates.get('gate_2_learned_compatibility_signal', {}).get('compatibility_TG_auc')}"
            ),
            "main_risk": "family/predicate shortcut and raw-witness construction provenance still need v2 controls",
            "promotion_gate": "family-controlled Task A with T+G beating source-only, T+Z, geometry-only, predicate/family, and shuffled/wrong-pair controls",
        },
        {
            "relation_family": "relative_vertical",
            "predicates": "higher than; lower than",
            "scope_status": "primary_v1_needs_expansion",
            "main_use": "directional geometry compatibility and predicate-flip/swap controls",
            "positive_tiers": "P1 audit/user-confirmed; P2 high-precision vertical-order verified; optional P0 GT+geometry-usable",
            "negative_tiers": "N3 higher/lower predicate flip; N4 subject/object swap; N1/N2 wrong or shuffled pair geometry; N6 same-rank hard negative",
            "allowed_g_e": "delta_z; top/bottom margins; vertical ordering; XY context; p_geom_valid only as baseline/teacher",
            "allowed_q_e": "geometry availability; vertical margin confidence; missing geometry",
            "current_evidence": f"prototype rows {prototype.get('counts', {}).get('by_family', {}).get('relative_vertical')}; current row count is smaller than support_contact",
            "main_risk": "small family count and possible predicate-direction shortcut",
            "promotion_gate": "expand v2 rows and show predicate flip / subject-object swap degradation without source-rank leakage",
        },
        {
            "relation_family": "attachment_like",
            "predicates": "attached to; hanging on; connected to",
            "scope_status": "diagnostic_hard_family",
            "main_use": "Q_e, observability, failure taxonomy, and optional future verified-positive pool",
            "positive_tiers": "P1 only if independently verified; current positive-anchor target is diagnostic-only",
            "negative_tiers": "N1/N2/N5 only after numeric/mesh/visual evidence is materialized independently",
            "allowed_g_e": "numeric attachment pair geometry only in diagnostic/pretraining conditions; no current p_rel target use",
            "allowed_q_e": "visual/mesh packet readiness; same-frame/crop/mesh/contact-sheet availability; uncertainty/abstain reasons",
            "current_evidence": (
                f"attachment smoke T+G AUROC {attach_gates.get('gate_2_compatibility_signal', {}).get('compatibility_TG_auc')}; "
                f"path decision {path_decision.get('selected_path')}"
            ),
            "main_risk": "target independence failed after positive-anchor repair; same-visible-pair controlled slice is too small",
            "promotion_gate": "new independent target with numeric G_e and clear controlled slices; otherwise diagnostic-only",
        },
        {
            "relation_family": "proximity",
            "predicates": "close by",
            "scope_status": "future_generality",
            "main_use": "generality branch after primary compatibility scope is stable",
            "positive_tiers": "P2 high-precision distance-verified; P0/P1 if audited",
            "negative_tiers": "N1/N2 wrong or shuffled geometry; N5 distance perturbation",
            "allowed_g_e": "boundary distance; center/XY distance; scale-normalized distance; footprint gap",
            "allowed_q_e": "geometry coverage and scene-scale normalization quality",
            "current_evidence": "previous H002 proximity branch was LH-heavy and not bidirectional under current queues",
            "main_risk": "dense relation noise and incomplete annotation make no-GT negative unsafe",
            "promotion_gate": "build a separate high-precision P2 target with hard distance perturbation controls",
        },
        {
            "relation_family": "relative_horizontal",
            "predicates": "left; right; front; behind",
            "scope_status": "deferred",
            "main_use": "not in v1 compatibility learning",
            "positive_tiers": "none for v1",
            "negative_tiers": "none for v1",
            "allowed_g_e": "requires explicit reference frame before use",
            "allowed_q_e": "reference-frame availability and ambiguity",
            "current_evidence": "not enough frame-grounded schema in current H002 artifacts",
            "main_risk": "view/world-frame ambiguity can dominate label semantics",
            "promotion_gate": "define reference-frame contract first",
        },
        {
            "relation_family": "containment",
            "predicates": "inside; surrounding",
            "scope_status": "deferred",
            "main_use": "not in v1 compatibility learning",
            "positive_tiers": "none for v1",
            "negative_tiers": "none for v1",
            "allowed_g_e": "containment ratio; volume overlap; boundary violation distance",
            "allowed_q_e": "mesh/point completeness sufficient for containment",
            "current_evidence": "not materialized in current prototype",
            "main_risk": "needs asymmetric containment geometry and object completeness",
            "promotion_gate": "materialize containment-specific G_e before target construction",
        },
    ]


def evidence_axis_contract() -> dict[str, Any]:
    return {
        "T_e": {
            "allowed": ["predicate label/text", "relation family", "subject/object class", "class text embeddings"],
            "blocked": ["source score", "source rank", "source id", "audit label", "GT match", "target construction key"],
        },
        "Z_e": {
            "allowed": ["source score", "source rank", "source id", "source calibration metadata"],
            "blocked_from": ["C_e compatibility head"],
            "use": "source baseline and final p_rel only",
        },
        "G_e": {
            "allowed": ["predicate-independent object-pair metric geometry", "raw witness v2 numeric fields", "point/mesh features when materialized"],
            "blocked": ["predicate", "relation family", "source score/rank", "audit/GT label", "construction proxy key"],
            "p_geom_valid_role": "baseline_or_teacher_not_main_input",
        },
        "C_e": {
            "definition": "compatibility(T_e, G_e)",
            "hard_rule": "must_not_use_Z_e",
            "primary_training": "P0/P1/P2 positives vs N1-N6 hard negatives with provenance tiers",
        },
        "Q_e": {
            "allowed": ["coverage", "missing geometry", "asset availability", "point/mesh/view quality", "evidence conflict"],
            "blocked": ["source confidence as uncertainty proxy", "audit accept/reject label", "construction key"],
            "use": "p_obs and selective decision, not direct relation truth",
        },
    }


def control_contract() -> dict[str, Any]:
    return {
        "minimum_controls": [
            "source_only_Z",
            "semantic_source_TZ_without_G",
            "geometry_only_G_without_T_or_Z",
            "compatibility_TG_without_Z",
            "full_TZGCQ_or_TZCQ",
            "predicate_family_shortcut",
            "source_rank_band_shortcut",
            "endpoint_label_pair_shortcut",
            "scan_or_instance_id_hidden_probe",
            "hidden_construction_proxy_probe",
            "wrong_pair_geometry",
            "shuffled_geometry",
            "predicate_flip_or_subject_object_swap_when_relation_directional",
        ],
        "promotion_gates": {
            "split": "train_internal_for_hypothesis; validation/test forbidden for construction",
            "class_mass": "primary Task A should have at least 60 positive and 60 negative rows overall and at least 30/30 for any reported primary family",
            "shortcut": "T+G must beat source-only, T+Z, predicate/family shortcut, and endpoint shortcut under grouped folds",
            "geometry_specificity": "wrong-pair or shuffled-geometry control must reduce compatibility score",
            "source_separation": "C_e condition must exclude Z_e; source shuffle control required before p_rel claim",
            "attachment_boundary": "attachment positive-anchor target remains diagnostic until a new independent controlled target passes",
        },
    }


def build_report(summary: dict[str, Any], family_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# H002 Compatibility Learning Scope Plan V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_scope = {summary['selected_scope']}",
        f"posterior_smoke_allowed = {summary['posterior_smoke_allowed']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Family Scope",
        "",
        "| Family | Status | Main Use | Main Risk |",
        "| --- | --- | --- | --- |",
    ]
    for row in family_rows:
        lines.append(f"| `{row['relation_family']}` | `{row['scope_status']}` | {row['main_use']} | {row['main_risk']} |")
    lines.extend(
        [
            "",
            "## Selected V1 Scope",
            "",
            "Primary H002 compatibility learning should focus on `support_contact` and `relative_vertical`.",
            "`support_contact` is the strongest current family because it has numeric raw-witness geometry and",
            "clear contact/support evidence. `relative_vertical` remains primary but needs v2 row expansion and",
            "directional controls such as predicate flip and subject/object swap.",
            "",
            "`attachment_like` is not discarded. It is frozen as a diagnostic hard family because the target-first",
            "repair route did not produce independent `p_rel/C_e` labels. Its packet evidence should be used for",
            "`Q_e`, observability, failure taxonomy, and future verified positives, not for a posterior smoke target.",
            "",
            "## Required Controls",
            "",
            "- `C_e` must use `T_e + G_e` only and must not use `Z_e`.",
            "- `G_e` must not contain predicate, relation family, source score/rank, audit label, or construction key.",
            "- H001 `p_geom_valid` is allowed only as baseline/teacher/ablation.",
            "- No-GT rows are not automatic negatives.",
            "- Every reported family needs source-only, semantic+source, geometry-only, predicate/family shortcut,",
            "  endpoint shortcut, hidden construction, wrong-pair/shuffled-geometry, and directional controls when applicable.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    path_decision = read_json(args.path_decision_dir / "summary.json")
    prototype = read_json(args.prototype_dir / "summary.json")
    smoke = read_json(args.smoke_dir / "summary.json")
    learned = read_json(args.learned_dir / "summary.json")
    attachment_smoke = read_json(args.attachment_smoke_dir / "summary.json")
    rows = read_jsonl(args.prototype_dir / "prototype_rows.jsonl")

    errors = validate_inputs(path_decision, prototype, smoke, learned, attachment_smoke)
    stats = row_family_stats(rows)
    family_rows = family_scope_rows(prototype, learned, attachment_smoke, path_decision)
    evidence_contract = evidence_axis_contract()
    controls = control_contract()
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_compatibility_learning_scope_inputs"

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_roots": {
            "path_decision": rel_path(args.path_decision_dir),
            "prototype": rel_path(args.prototype_dir),
            "smoke": rel_path(args.smoke_dir),
            "learned": rel_path(args.learned_dir),
            "attachment_smoke": rel_path(args.attachment_smoke_dir),
        },
        "validation_errors": len(errors),
        "selected_scope": "primary_support_contact_relative_vertical_attachment_diagnostic",
        "next_todo": next_todo,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "family_stats": stats,
        "family_scope": family_rows,
        "evidence_axis_contract": evidence_contract,
        "control_contract": controls,
        "key_decisions": {
            "primary_families_v1": ["support_contact", "relative_vertical"],
            "diagnostic_hard_families": ["attachment_like"],
            "future_generality_families": ["proximity"],
            "deferred_families": ["relative_horizontal", "containment"],
            "why_attachment_not_primary": "positive-anchor class mass passed, but target independence failed and no controlled slice cleared",
            "why_more_posterior_not_next": "bottleneck is scope/provenance/controls, not model capacity",
        },
        "boundary": {
            "split": "train_only_hypothesis_artifacts",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "scope_plan": rel_path(args.output_dir / "scope_plan.json"),
            "family_scope": rel_path(args.output_dir / "family_scope.csv"),
            "evidence_axis_contract": rel_path(args.output_dir / "evidence_axis_contract.json"),
            "control_contract": rel_path(args.output_dir / "control_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    scope_plan = {
        "selected_scope": summary["selected_scope"],
        "next_todo": next_todo,
        "family_scope": family_rows,
        "evidence_axis_contract": evidence_contract,
        "control_contract": controls,
        "key_decisions": summary["key_decisions"],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "scope_plan.json", scope_plan)
    write_csv(args.output_dir / "family_scope.csv", family_rows)
    write_json(args.output_dir / "evidence_axis_contract.json", evidence_contract)
    write_json(args.output_dir / "control_contract.json", controls)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary, family_rows), encoding="utf-8")

    print(f"status={status}")
    print(f"selected_scope={summary['selected_scope']}")
    print(f"next={next_todo}")
    print(f"primary_families={','.join(summary['key_decisions']['primary_families_v1'])}")
    print(f"diagnostic_families={','.join(summary['key_decisions']['diagnostic_hard_families'])}")
    print(f"validation_errors={len(errors)}")


if __name__ == "__main__":
    main()
