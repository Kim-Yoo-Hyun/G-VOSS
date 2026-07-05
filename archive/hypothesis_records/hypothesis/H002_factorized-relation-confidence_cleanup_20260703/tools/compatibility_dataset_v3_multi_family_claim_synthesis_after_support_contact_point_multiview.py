#!/usr/bin/env python3
"""Synthesize current H002 multi-family claim after support/contact review."""

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
DEFAULT_SUPPORT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
)
DEFAULT_CLOSE_BY_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
)
DEFAULT_ATTACHMENT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion"
)
DEFAULT_SCOPE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview"
)

EXPECTED_RELATIVE_STATUS = "h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe"
EXPECTED_SUPPORT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis"
)
EXPECTED_SUPPORT_NEXT = "compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview"
EXPECTED_CLOSE_BY_STATUS = "h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe"
EXPECTED_ATTACHMENT_STATUS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic"
EXPECTED_SCOPE_STATUS = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_v1"
STATUS_READY = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_input_errors"
SELECTED_PATH = "freeze_relation_aware_compatibility_routing_claim_select_ablation_table_plan"
NEXT_TODO = "compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relative-dir", type=Path, default=DEFAULT_RELATIVE_DIR)
    parser.add_argument("--support-dir", type=Path, default=DEFAULT_SUPPORT_DIR)
    parser.add_argument("--close-by-dir", type=Path, default=DEFAULT_CLOSE_BY_DIR)
    parser.add_argument("--attachment-dir", type=Path, default=DEFAULT_ATTACHMENT_DIR)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def validation_rows(root: Path) -> list[dict[str, Any]]:
    return read_jsonl(root / "validation_errors.jsonl")


def validate_inputs(
    relative: dict[str, Any],
    support: dict[str, Any],
    close_by: dict[str, Any],
    attachment: dict[str, Any],
    scope: dict[str, Any],
    support_claim: dict[str, Any],
    support_relation_routes: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "relative": (relative, EXPECTED_RELATIVE_STATUS),
        "support": (support, EXPECTED_SUPPORT_STATUS),
        "close_by": (close_by, EXPECTED_CLOSE_BY_STATUS),
        "attachment": (attachment, EXPECTED_ATTACHMENT_STATUS),
        "scope": (scope, EXPECTED_SCOPE_STATUS),
    }
    for name, (summary, status) in expected.items():
        if summary.get("status") != status:
            errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
        if summary.get("validation_errors") != 0:
            errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
        rows = validation_rows(roots[name])
        if rows:
            errors.append({"input": name, "error_type": "validation_error_rows_present", "rows": len(rows)})
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append({"input": name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if support.get("next_todo") != EXPECTED_SUPPORT_NEXT:
        errors.append({"input": "support", "error_type": "unexpected_next_todo", "actual": support.get("next_todo")})
    if support_claim.get("accepted_paper_role") != "support/contact compatibility-route evidence with caveat":
        errors.append({"input": "support_claim", "error_type": "unexpected_accepted_role", "actual": support_claim.get("accepted_paper_role")})
    route_status = {row.get("relation_family"): row.get("status") for row in support_relation_routes}
    if route_status.get("support_contact") != "retain_main_route_with_caveat":
        errors.append({"input": "support_relation_routes", "error_type": "support_contact_not_retained_with_caveat", "routes": route_status})

    rel_mech = relative.get("mechanism_result", {})
    if rel_mech.get("accepted") is not True or float(rel_mech.get("primary_auroc", 0.0)) < 0.90:
        errors.append({"input": "relative", "error_type": "relative_vertical_not_clean_mechanism", "mechanism": rel_mech})
    support_numbers = support_claim.get("main_numbers", {})
    if float(support_numbers.get("M8_TG_point_contact_interaction", 0.0)) < 0.65:
        errors.append({"input": "support", "error_type": "support_signal_too_low", "numbers": support_numbers})
    if float(support_numbers.get("C1_wrong_T_same_G", 1.0)) >= 0.5:
        errors.append({"input": "support", "error_type": "support_wrong_t_not_collapsed", "numbers": support_numbers})
    return errors


def claim_skeleton() -> dict[str, Any]:
    return {
        "working_title": "Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations",
        "claim_type": "hypothesis-stage paper-framework skeleton",
        "short_claim": "relation-aware predicate-geometry compatibility routing",
        "core_problem": (
            "3D scene graph relation sources expose a single confidence score, but relation reliability "
            "depends on semantic content, predicate-independent geometry evidence, compatibility between "
            "the predicate and geometry, and evidence observability."
        ),
        "core_claim": (
            "Relation reliability should be estimated through relation-aware evidence routes. "
            "Some families are geometry-decidable controls, some require explicit predicate-geometry "
            "compatibility, and some must abstain or defer until observability evidence is available."
        ),
        "factor_contract": {
            "T_e": "semantic content: predicate and subject/object class semantics",
            "Z_e": "source confidence/rank; allowed for final reliability but excluded from C_e",
            "G_e": "predicate-independent geometry evidence",
            "C_e": "predicate-geometry compatibility, learned from T_e and G_e without Z_e",
            "Q_e": "observability/evidence quality, used for p_obs/selective decision, not truth",
            "p_obs": "probability that available evidence is sufficient to decide",
            "p_rel": "relation reliability when evidence is observable",
        },
        "main_contribution_candidates": [
            "factorized relation evidence representation for 3D scene graph edges",
            "predicate-geometry compatibility learning separated from source confidence",
            "relation-aware evidence routing across physical relation families",
            "counterfactual controls: wrong predicate, shuffled geometry, geometry-only, semantic-only, and concat baselines",
            "failure taxonomy showing when geometry-easy, compatibility-heavy, and observability-heavy routes are appropriate",
        ],
        "current_allowed_claim": (
            "H002 currently supports a train-only mechanism claim: relative_vertical provides clean C_e evidence, "
            "and support_contact provides challenging compatibility-route evidence with caveat."
        ),
        "blocked_claims": [
            "paper-level performance",
            "held-out/test relation reliability",
            "all relation-family generality",
            "support/contact fully solved",
            "Q_e as relation truth",
            "final calibrated p_rel/p_obs results",
        ],
    }


def evidence_table(relative: dict[str, Any], support_claim: dict[str, Any]) -> list[dict[str, Any]]:
    rel = relative.get("mechanism_result", {})
    nums = support_claim.get("main_numbers", {})
    return [
        {
            "family": "relative_vertical",
            "predicates": "higher than; lower than",
            "route_type": "clean compatibility mechanism",
            "primary_signal": rel.get("primary_auroc"),
            "semantic_only": "near chance / source-safe baseline",
            "geometry_only": rel.get("geometry_only_auroc"),
            "plain_concat": rel.get("plain_concat_auroc"),
            "wrong_T": rel.get("wrong_t_auroc"),
            "shuffled_G": f"{rel.get('shuffled_g_global_auroc')} / {rel.get('shuffled_g_within_predicate_auroc')}",
            "paper_role": "main mechanism evidence",
            "caveat": "controlled/easy vertical compatibility, not final reliability",
        },
        {
            "family": "support_contact",
            "predicates": "lying on; standing on",
            "route_type": "challenging compatibility route",
            "primary_signal": nums.get("M8_TG_point_contact_interaction"),
            "semantic_only": nums.get("M1_semantic_only_T"),
            "geometry_only": nums.get("M5_point_contact_geometry"),
            "plain_concat": nums.get("M7_TG_point_contact_concat"),
            "wrong_T": nums.get("C1_wrong_T_same_G"),
            "shuffled_G": f"{nums.get('C2_shuffled_G_global')} / {nums.get('C3_shuffled_G_within_predicate')}",
            "paper_role": "main route evidence with caveat",
            "caveat": "near-threshold and challenging; not fully solved",
        },
        {
            "family": "proximity",
            "predicates": "close by",
            "route_type": "geometry-easy control",
            "primary_signal": "distance/rule geometry solves current target",
            "semantic_only": "not main",
            "geometry_only": "dominant",
            "plain_concat": "not needed",
            "wrong_T": "not applicable as single predicate",
            "shuffled_G": "diagnostic only",
            "paper_role": "generality/control, not main compatibility proof",
            "caveat": "risks becoming a distance verifier",
        },
        {
            "family": "attachment_like",
            "predicates": "attached to; hanging on; connected to",
            "route_type": "observability-heavy future route",
            "primary_signal": "diagnostic targets blocked by shortcut/observability",
            "semantic_only": "not enough",
            "geometry_only": "not enough",
            "plain_concat": "not enough",
            "wrong_T": "future",
            "shuffled_G": "future",
            "paper_role": "future/diagnostic",
            "caveat": "needs visual/mesh evidence and independent target",
        },
    ]


def family_route_table() -> list[dict[str, Any]]:
    return [
        {
            "family": "relative_vertical",
            "route": "clean compatibility mechanism",
            "predicates": "higher than; lower than",
            "use_in_claim": "main",
            "evidence_route": "T_e x signed vertical G_e",
            "p_obs_role": "low emphasis; geometry evidence available",
            "risk": "too clean if used alone",
            "decision": "retain as clean mechanism anchor",
        },
        {
            "family": "support_contact",
            "route": "challenging compatibility route",
            "predicates": "lying on; standing on",
            "use_in_claim": "main_with_caveat",
            "evidence_route": "T_e x point/contact/pose G_e",
            "p_obs_role": "important; sufficient rows much cleaner than limited rows",
            "risk": "lying-on ambiguity and near-threshold aggregate AUROC",
            "decision": "retain as challenging route evidence",
        },
        {
            "family": "support_contact_superordinate",
            "route": "diagnostic taxonomy",
            "predicates": "supported by",
            "use_in_claim": "diagnostic",
            "evidence_route": "support/contact G_e overlaps lying/standing states",
            "p_obs_role": "diagnostic",
            "risk": "superordinate label cannot be clean negative",
            "decision": "defer primary claim",
        },
        {
            "family": "proximity",
            "route": "geometry-easy control",
            "predicates": "close by",
            "use_in_claim": "control_or_generality",
            "evidence_route": "distance geometry",
            "p_obs_role": "low emphasis under current target",
            "risk": "geometry-only dominance",
            "decision": "diagnostic only",
        },
        {
            "family": "attachment_like",
            "route": "observability-heavy future",
            "predicates": "attached to; hanging on; connected to",
            "use_in_claim": "future_or_diagnostic",
            "evidence_route": "visual/mesh contact + Q_e required",
            "p_obs_role": "central",
            "risk": "target independence and visibility bottleneck",
            "decision": "defer until deployable visual/mesh evidence",
        },
        {
            "family": "relative_horizontal",
            "route": "reference-frame deferred",
            "predicates": "left; right; front; behind",
            "use_in_claim": "future",
            "evidence_route": "requires coordinate/viewer/reference-frame contract",
            "p_obs_role": "undefined",
            "risk": "frame ambiguity",
            "decision": "defer",
        },
    ]


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "support/contact AUROC is moderate",
            "severity": "high",
            "answer": "Do not claim solved support/contact. Use it as challenging route evidence because controls establish interaction necessity.",
            "needed_artifact": "support/contact failure analysis and route review",
        },
        {
            "risk": "relative_vertical is too clean",
            "severity": "medium",
            "answer": "Use it as the clean mechanism anchor, not as sole evidence. Pair it with support/contact.",
            "needed_artifact": "multi-family route table",
        },
        {
            "risk": "close by is just distance",
            "severity": "medium",
            "answer": "Keep proximity as geometry-easy control/generality, not main C_e proof.",
            "needed_artifact": "proximity path decision",
        },
        {
            "risk": "attachment/hanging are not solved",
            "severity": "medium",
            "answer": "Mark attachment-like relations as observability-heavy future route requiring visual/mesh evidence.",
            "needed_artifact": "attachment diagnostic freeze",
        },
        {
            "risk": "Q_e may be truth leakage",
            "severity": "high",
            "answer": "Q_e does not improve M9 over M8 in support/contact and shuffled-Q is similar; use Q_e for p_obs/selective decision only.",
            "needed_artifact": "support/contact failure analysis",
        },
        {
            "risk": "no paper-level held-out/Docker result",
            "severity": "high",
            "answer": "Correct. This is H002 hypothesis-stage synthesis. Paper promotion requires held-out/Docker protocol.",
            "needed_artifact": "ablation/table plan next",
        },
        {
            "risk": "factorized formulation looks like reworded concatenation",
            "severity": "high",
            "answer": "Main evidence is not concatenation; plain T+G concat fails in both main routes, while interaction and controls show alignment-specific signal.",
            "needed_artifact": "ablation table with concat and controls",
        },
    ]


def route_decisions() -> list[dict[str, Any]]:
    return [
        {
            "route": "freeze_relation_aware_compatibility_routing_claim",
            "verdict": "selected",
            "reason": "Current evidence supports a route-based C_e mechanism over two physical relation families.",
            "next_action": "use as H002 paper-framework skeleton",
        },
        {
            "route": "claim_broad_relation_reliability_now",
            "verdict": "reject",
            "reason": "No held-out p_rel/p_obs reliability target has passed.",
            "next_action": "keep reliability blocked",
        },
        {
            "route": "add_more_relation_families_immediately",
            "verdict": "defer",
            "reason": "Current bottleneck is paper-framework/table design, not absence of another diagnostic family.",
            "next_action": "return after ablation/table plan",
        },
        {
            "route": "use_support_contact_as_fully_solved",
            "verdict": "reject",
            "reason": "Support/contact is near-threshold and challenging, though it shows strong route evidence.",
            "next_action": "use caveated wording",
        },
        {
            "route": "promote_Qe_as_truth",
            "verdict": "reject",
            "reason": "Q_e is observability/p_obs evidence; it should not decide relation truth directly.",
            "next_action": "separate p_obs and p_rel in table plan",
        },
        {
            "route": "ablation_and_table_plan",
            "verdict": "selected_next",
            "reason": "Need to convert the claim skeleton into main tables, ablations, controls, and promotion gates.",
            "next_action": NEXT_TODO,
        },
    ]


def paper_framework_skeleton() -> str:
    return """# H002 Paper Framework Skeleton

## Working Title

Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations

## Core Problem

3D scene graph relation sources provide a single relation confidence, but that
confidence conflates semantic plausibility, source prior, geometric evidence,
predicate-geometry compatibility, and evidence observability.

## Core Thesis

Relation reliability should be modeled through relation-aware evidence routes.
Geometry-easy relations can be handled by direct geometric evidence, compatibility-heavy
relations require an explicit `T_e x G_e` compatibility factor, and observability-heavy
relations should defer or abstain until adequate visual/mesh evidence is available.

## Method Skeleton

```text
T_e: semantic content
Z_e: source confidence / rank
G_e: predicate-independent geometry evidence
C_e: compatibility(T_e, G_e), excluding Z_e
Q_e: evidence quality / observability
p_obs: whether evidence is sufficient to decide
p_rel: relation reliability when observable
```

## Current Evidence Roles

- `relative_vertical`: clean C_e mechanism anchor.
- `support_contact`: challenging compatibility-route evidence with caveat.
- `proximity`: geometry-easy diagnostic/control.
- `attachment_like`: observability-heavy future route.
- `relative_horizontal`: reference-frame deferred.

## Current Claim Boundary

Allowed:

```text
H002 supports a relation-aware predicate-geometry compatibility mechanism over
two physical relation routes, with support/contact showing challenging but
control-backed interaction evidence.
```

Blocked:

```text
broad relation reliability
paper-level held-out performance
support/contact fully solved
all-family generality
Q_e as truth signal
```

## Next Required Paper-Level Work

The next step is an ablation/table plan that defines which rows become main
mechanism evidence, which rows stay diagnostic, what controls are mandatory,
and what held-out/Docker gates are required before paper promotion.
"""


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Convert the multi-family claim skeleton into a concrete main-table, ablation, control, and promotion-gate plan.",
        "must_define": [
            "main mechanism table rows",
            "diagnostic route table rows",
            "semantic-only, geometry-only, concat, interaction, wrong-T, shuffled-G controls",
            "Q_e/p_obs table position",
            "paper-level held-out/Docker promotion gates",
            "forbidden wording and caveat wording",
        ],
        "must_not_do": [
            "do not add another relation family before table plan",
            "do not promote H002 as paper evidence yet",
            "do not merge Q_e into relation truth",
            "do not rewrite support/contact internal near-threshold status",
        ],
    }


def write_report(path: Path, summary: dict[str, Any], claim: dict[str, Any], evidence: list[dict[str, Any]], routes: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Multi-Family Claim Synthesis After Support/Contact Point/Multiview",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Claim Skeleton",
        "",
        f"- short claim: `{claim['short_claim']}`",
        f"- claim type: `{claim['claim_type']}`",
        "",
        "Allowed claim:",
        "",
        f"> {claim['current_allowed_claim']}",
        "",
        "Blocked claims:",
        "",
    ]
    for item in claim["blocked_claims"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Evidence Table",
            "",
            "| Family | Route | Primary | G-only | Concat | Wrong-T | Shuffled-G | Role |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in evidence:
        lines.append(
            f"| `{row['family']}` | {row['route_type']} | {row['primary_signal']} | "
            f"{row['geometry_only']} | {row['plain_concat']} | {row['wrong_T']} | {row['shuffled_G']} | {row['paper_role']} |"
        )
    lines.extend(
        [
            "",
            "## Route Decisions",
            "",
            "| Route | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in routes:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "H002 should now be framed as relation-aware compatibility routing. The current evidence",
            "does not justify a broad reliability claim, but it does justify a mechanism-level framework",
            "where relation families require different evidence routes.",
            "",
            "The next step is not another model run. It is an ablation/table plan that specifies exactly",
            "which comparisons and controls would make the framework paper-ready.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    relative = read_json(args.relative_dir / "summary.json")
    support = read_json(args.support_dir / "summary.json")
    support_claim = read_json(args.support_dir / "claim_position.json")
    support_relation_routes = read_csv(args.support_dir / "relation_route_table.csv")
    close_by = read_json(args.close_by_dir / "summary.json")
    attachment = read_json(args.attachment_dir / "summary.json")
    scope = read_json(args.scope_dir / "summary.json")
    roots = {
        "relative": args.relative_dir,
        "support": args.support_dir,
        "close_by": args.close_by_dir,
        "attachment": args.attachment_dir,
        "scope": args.scope_dir,
    }
    errors = validate_inputs(relative, support, close_by, attachment, scope, support_claim, support_relation_routes, roots)

    claim = claim_skeleton()
    evidence = evidence_table(relative, support_claim)
    family_routes = family_route_table()
    risks = reviewer_risks()
    routes = route_decisions()
    next_contract = next_plan_contract()

    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "split": "train_only_claim_synthesis",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "claim_boundary": claim,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {name: rel_path(path) for name, path in roots.items()},
        "next_todo": NEXT_TODO if not errors else "fix_multi_family_claim_synthesis_inputs",
        "output_paths": {
            "claim_skeleton": rel_path(args.output_dir / "claim_skeleton.json"),
            "evidence_table": rel_path(args.output_dir / "evidence_table.csv"),
            "family_route_table": rel_path(args.output_dir / "family_route_table.csv"),
            "framework_skeleton": rel_path(args.output_dir / "framework_skeleton.md"),
            "next_plan_contract": rel_path(args.output_dir / "next_plan_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "reviewer_risk_table": rel_path(args.output_dir / "reviewer_risk_table.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH if not errors else "fix_inputs_before_claim_synthesis",
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
    }

    write_json(args.output_dir / "claim_skeleton.json", claim)
    write_csv(args.output_dir / "evidence_table.csv", evidence)
    write_csv(args.output_dir / "family_route_table.csv", family_routes)
    (args.output_dir / "framework_skeleton.md").write_text(paper_framework_skeleton(), encoding="utf-8")
    write_json(args.output_dir / "next_plan_contract.json", next_contract)
    write_csv(args.output_dir / "reviewer_risk_table.csv", risks)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, claim, evidence, routes)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
