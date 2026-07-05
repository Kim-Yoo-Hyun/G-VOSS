#!/usr/bin/env python3
"""Update H002 multi-family synthesis after the size-relative result review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PREV_SYNTHESIS_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview"
)
DEFAULT_SIZE_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner"
DEFAULT_RELATIVE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision"
DEFAULT_SUPPORT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
)
DEFAULT_CLOSE_BY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative"

EXPECTED_PREV_SYNTHESIS_STATUS = (
    "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready"
)
EXPECTED_SIZE_STATUS = (
    "h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update"
)
EXPECTED_SIZE_NEXT = "compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative"
EXPECTED_RELATIVE_STATUS = "h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe"
EXPECTED_SUPPORT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis"
)
EXPECTED_CLOSE_BY_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_v1"
STATUS_READY = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_input_errors"
SELECTED_PATH = "update_relation_aware_compatibility_routing_claim_with_size_relative_select_table_plan_update"
NEXT_TODO = "compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-synthesis-dir", type=Path, default=DEFAULT_PREV_SYNTHESIS_DIR)
    parser.add_argument("--size-review-dir", type=Path, default=DEFAULT_SIZE_REVIEW_DIR)
    parser.add_argument("--relative-dir", type=Path, default=DEFAULT_RELATIVE_DIR)
    parser.add_argument("--support-dir", type=Path, default=DEFAULT_SUPPORT_DIR)
    parser.add_argument("--close-by-dir", type=Path, default=DEFAULT_CLOSE_BY_DIR)
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    previous: dict[str, Any],
    size: dict[str, Any],
    relative: dict[str, Any],
    support: dict[str, Any],
    close_by: dict[str, Any],
    size_routes: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "previous_synthesis": (previous, EXPECTED_PREV_SYNTHESIS_STATUS),
        "size_review": (size, EXPECTED_SIZE_STATUS),
        "relative": (relative, EXPECTED_RELATIVE_STATUS),
        "support": (support, EXPECTED_SUPPORT_STATUS),
        "close_by": (close_by, EXPECTED_CLOSE_BY_STATUS),
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

    if size.get("next_todo") != EXPECTED_SIZE_NEXT:
        errors.append({"input": "size_review", "error_type": "unexpected_next_todo", "actual": size.get("next_todo")})

    size_route = {row.get("relation_family"): row for row in size_routes}
    if size_route.get("size_relative", {}).get("route_role") != "main_compatibility_route_mechanism_evidence":
        errors.append({"input": "size_routes", "error_type": "size_relative_not_main_mechanism", "routes": size_route})
    if float(size.get("runner_snapshot", {}).get("primary_auroc", 0.0)) < 0.95:
        errors.append({"input": "size_review", "error_type": "size_primary_too_low", "snapshot": size.get("runner_snapshot")})
    if float(size.get("runner_snapshot", {}).get("geometry_only_auroc", 1.0)) > 0.60:
        errors.append({"input": "size_review", "error_type": "size_geometry_only_too_high", "snapshot": size.get("runner_snapshot")})
    if float(size.get("runner_snapshot", {}).get("concat_auroc", 1.0)) > 0.60:
        errors.append({"input": "size_review", "error_type": "size_concat_too_high", "snapshot": size.get("runner_snapshot")})
    return errors


def claim_skeleton() -> dict[str, Any]:
    return {
        "working_title": "Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations",
        "claim_type": "hypothesis-stage paper-framework skeleton",
        "short_claim": "relation-aware predicate-geometry compatibility routing",
        "core_problem": (
            "A 3D scene graph relation source exposes one relation confidence, but relation reliability "
            "depends on semantic content, source confidence, predicate-independent geometry evidence, "
            "predicate-geometry compatibility, and evidence observability."
        ),
        "core_claim": (
            "Relation reliability should be estimated through relation-aware evidence routes. "
            "Relative-direction and size-relative families provide clean predicate-conditioned geometry "
            "compatibility evidence, support/contact provides a challenging compatibility route with caveat, "
            "proximity is a geometry-easy control, and attachment-like relations remain observability-heavy."
        ),
        "factor_contract": {
            "T_e": "semantic content: predicate and subject/object class semantics",
            "Z_e": "source confidence/rank; allowed for final reliability but excluded from C_e",
            "G_e": "predicate-independent geometry evidence",
            "C_e": "compatibility(T_e, G_e), excluding Z_e",
            "Q_e": "observability/evidence quality, used for p_obs/selective decision, not relation truth",
            "p_obs": "probability that available evidence is sufficient to decide",
            "p_rel": "relation reliability when evidence is observable",
        },
        "current_allowed_claim": (
            "H002 currently supports a train-only mechanism claim: relation families require different "
            "evidence routes, and clean size/vertical routes plus challenging support/contact controls "
            "support explicit predicate-geometry compatibility rather than fixed score fusion."
        ),
        "blocked_claims": [
            "paper-level performance",
            "held-out/test relation reliability",
            "all relation-family generality",
            "support/contact fully solved",
            "Q_e as relation truth",
            "final calibrated p_rel/p_obs results",
            "geometry-only reliability framework",
        ],
    }


def evidence_table(
    old_evidence: list[dict[str, str]],
    size_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    snapshot = size_summary["runner_snapshot"]
    rows: list[dict[str, Any]] = []
    inserted = False
    for row in old_evidence:
        rows.append(dict(row))
        if row.get("family") == "relative_vertical":
            rows.append(
                {
                    "family": "size_relative",
                    "predicates": "bigger than; smaller than",
                    "route_type": "clean compatibility mechanism",
                    "primary_signal": f"{snapshot['primary_auroc']:.6f}",
                    "semantic_only": f"{snapshot['semantic_only_auroc']:.6f}",
                    "geometry_only": f"{snapshot['geometry_only_auroc']:.6f}",
                    "plain_concat": f"{snapshot['concat_auroc']:.6f}",
                    "wrong_T": f"{snapshot['wrong_t_auroc']:.6f}",
                    "shuffled_G": f"{snapshot['shuffled_g_global_auroc']:.6f} / {snapshot['shuffled_g_within_predicate_auroc']:.6f}",
                    "paper_role": "main mechanism evidence with calibration caveat",
                    "caveat": "clean deterministic size relation; not calibrated probability or paper-level result",
                }
            )
            inserted = True
    if not inserted:
        rows.append(
            {
                "family": "size_relative",
                "predicates": "bigger than; smaller than",
                "route_type": "clean compatibility mechanism",
                "primary_signal": f"{snapshot['primary_auroc']:.6f}",
                "semantic_only": f"{snapshot['semantic_only_auroc']:.6f}",
                "geometry_only": f"{snapshot['geometry_only_auroc']:.6f}",
                "plain_concat": f"{snapshot['concat_auroc']:.6f}",
                "wrong_T": f"{snapshot['wrong_t_auroc']:.6f}",
                "shuffled_G": f"{snapshot['shuffled_g_global_auroc']:.6f} / {snapshot['shuffled_g_within_predicate_auroc']:.6f}",
                "paper_role": "main mechanism evidence with calibration caveat",
                "caveat": "clean deterministic size relation; not calibrated probability or paper-level result",
            }
        )
    return rows


def family_route_table(old_routes: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inserted = False
    for row in old_routes:
        rows.append(dict(row))
        if row.get("family") == "relative_vertical":
            rows.append(
                {
                    "family": "size_relative",
                    "route": "clean compatibility mechanism",
                    "predicates": "bigger than; smaller than",
                    "use_in_claim": "main",
                    "evidence_route": "T_e x object-size-ratio G_e",
                    "p_obs_role": "low emphasis; semseg OBB geometry available",
                    "risk": "too deterministic if used alone",
                    "decision": "retain as second clean mechanism anchor with calibration caveat",
                }
            )
            inserted = True
    if not inserted:
        rows.append(
            {
                "family": "size_relative",
                "route": "clean compatibility mechanism",
                "predicates": "bigger than; smaller than",
                "use_in_claim": "main",
                "evidence_route": "T_e x object-size-ratio G_e",
                "p_obs_role": "low emphasis; semseg OBB geometry available",
                "risk": "too deterministic if used alone",
                "decision": "retain as second clean mechanism anchor with calibration caveat",
            }
        )
    return rows


def reviewer_risks(old_risks: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = list(old_risks)
    rows.extend(
        [
            {
                "risk": "size_relative is too deterministic",
                "severity": "medium",
                "answer": (
                    "Use it as a clean C_e mechanism/control route, not as the only novelty evidence. "
                    "The value is that T-only, G-only, and concat fail while T_e x G_e succeeds under wrong-T and shuffled-G controls."
                ),
                "needed_artifact": "size-relative result review and updated multi-family route table",
            },
            {
                "risk": "clean vertical and size routes make H002 look rule-based",
                "severity": "medium",
                "answer": (
                    "State that clean routes identify the mechanism, while support/contact shows the challenging compatibility route. "
                    "Proximity and attachment-like routes define boundary conditions."
                ),
                "needed_artifact": "updated evidence table with support/contact and diagnostic families",
            },
            {
                "risk": "high AUROC implies calibrated reliability",
                "severity": "high_if_overclaimed",
                "answer": "Do not claim calibration. Size-relative ECE is high, so p_rel/p_obs remains blocked.",
                "needed_artifact": "claim boundary table and calibration caveat",
            },
        ]
    )
    return rows


def route_decisions() -> list[dict[str, Any]]:
    return [
        {
            "route": "update_relation_aware_compatibility_routing_claim_with_size_relative",
            "verdict": "selected",
            "reason": "size_relative adds a second clean C_e mechanism route beyond relative_vertical.",
            "next_action": "update table/ablation plan to include size_relative",
        },
        {
            "route": "claim_universal_relation_reliability",
            "verdict": "reject",
            "reason": "no calibrated p_rel/p_obs or held-out reliability target has passed.",
            "next_action": "keep reliability and calibration claims blocked",
        },
        {
            "route": "claim_geometry_only_framework",
            "verdict": "reject",
            "reason": "size_relative geometry-only AUROC is chance; the evidence supports predicate-conditioned compatibility.",
            "next_action": "keep T_e x G_e controls central",
        },
        {
            "route": "add_more_relation_families_before_table_update",
            "verdict": "defer",
            "reason": "current bottleneck is integrating the new family into the route/table framework.",
            "next_action": "return after updated table plan if reviewer coverage remains weak",
        },
        {
            "route": "ablation_and_table_plan_update_after_size_relative",
            "verdict": "selected_next",
            "reason": "the previous table plan predates size_relative and must be refreshed.",
            "next_action": NEXT_TODO,
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Update the H002 table and ablation contract after adding size_relative to the multi-family route synthesis.",
        "must_include": [
            "relative_vertical clean compatibility row",
            "size_relative clean compatibility row",
            "support_contact challenging compatibility row with caveat",
            "proximity geometry-easy diagnostic/control row",
            "attachment_like observability-heavy deferred row",
            "semantic-only, geometry-only, no-interaction concat, T_e x G_e interaction, wrong-T, shuffled-G, and sign-flip controls where applicable",
            "calibration caveat for high-AUROC but high-ECE smoke results",
        ],
        "must_not_do": [
            "do not promote to paper-level result",
            "do not claim calibrated p_rel or p_obs",
            "do not treat Q_e as relation truth",
            "do not hide support/contact near-threshold caveat",
            "do not call clean size/vertical routes universal relation generalization",
        ],
    }


def framework_skeleton() -> str:
    return """# H002 Framework Skeleton After Size-Relative Synthesis

## Working Title

Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations

## Core Thesis

Relation reliability should not be estimated by a fixed semantic-geometry score
fusion. H002 represents relation edges through separated factors and routes each
relation family through the evidence path that is actually meaningful for that
family.

```text
T_e = semantic content
Z_e = source confidence
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e), without Z_e
Q_e = observability / evidence quality
p_obs = whether evidence is sufficient to decide
p_rel = relation reliability when observable
```

## Current Family Routes

- `relative_vertical`: clean compatibility route.
- `size_relative`: clean compatibility route using object-size geometry.
- `support_contact`: challenging compatibility route with point/contact/pose evidence.
- `proximity`: geometry-easy control under the current `close by` target.
- `attachment_like`: observability-heavy future/deferred route.
- `relative_horizontal`: reference-frame deferred route.

## Allowed Claim

H002 currently supports a train-only mechanism claim: relation families require
different evidence routes, and explicit `T_e x G_e` compatibility is necessary in
clean size/vertical families and useful in challenging support/contact relations.

## Blocked Claims

- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- universal all-family generality
- support/contact fully solved
- geometry-only relation reliability
"""


def write_report(
    path: Path,
    summary: dict[str, Any],
    claim: dict[str, Any],
    evidence: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> None:
    lines = [
        "# Multi-Family Claim Synthesis After Size-Relative",
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
        "## Updated Claim",
        "",
        claim["current_allowed_claim"],
        "",
        "Blocked claims remain:",
        "",
    ]
    for item in claim["blocked_claims"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Updated Evidence Table",
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
            "`size_relative` strengthens the clean compatibility-route side of H002 because the same",
            "geometry evidence becomes valid or invalid depending on the predicate. It does not make",
            "H002 a geometry-only method, because geometry-only and no-interaction concat remain at",
            "chance for the size-relative target.",
            "",
            "The next step is to update the ablation/table plan so the H002 framework has a current",
            "main-mechanism table, diagnostic route table, and promotion-gate list that include",
            "`size_relative`.",
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

    previous = read_json(args.previous_synthesis_dir / "summary.json")
    old_evidence = read_csv(args.previous_synthesis_dir / "evidence_table.csv")
    old_routes = read_csv(args.previous_synthesis_dir / "family_route_table.csv")
    old_risks = read_csv(args.previous_synthesis_dir / "reviewer_risk_table.csv")
    size = read_json(args.size_review_dir / "summary.json")
    size_routes = read_csv(args.size_review_dir / "route_position.csv")
    relative = read_json(args.relative_dir / "summary.json")
    support = read_json(args.support_dir / "summary.json")
    close_by = read_json(args.close_by_dir / "summary.json")

    roots = {
        "previous_synthesis": args.previous_synthesis_dir,
        "size_review": args.size_review_dir,
        "relative": args.relative_dir,
        "support": args.support_dir,
        "close_by": args.close_by_dir,
    }
    errors = validate_inputs(previous, size, relative, support, close_by, size_routes, roots)

    claim = claim_skeleton()
    evidence = evidence_table(old_evidence, size)
    families = family_route_table(old_routes)
    risks = reviewer_risks(old_risks)
    decisions = route_decisions()
    next_contract = next_plan_contract()

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "previous_synthesis": rel_path(args.previous_synthesis_dir),
            "size_review": rel_path(args.size_review_dir),
            "relative": rel_path(args.relative_dir),
            "support": rel_path(args.support_dir),
            "close_by": rel_path(args.close_by_dir),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "claim_skeleton": rel_path(args.output_dir / "claim_skeleton.json"),
            "evidence_table": rel_path(args.output_dir / "evidence_table.csv"),
            "family_route_table": rel_path(args.output_dir / "family_route_table.csv"),
            "reviewer_risk_table": rel_path(args.output_dir / "reviewer_risk_table.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "framework_skeleton": rel_path(args.output_dir / "framework_skeleton.md"),
            "next_plan_contract": rel_path(args.output_dir / "next_plan_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "evidence_rows": len(evidence),
            "family_route_rows": len(families),
            "reviewer_risk_rows": len(risks),
            "route_decision_rows": len(decisions),
        },
        "claim_boundary": claim,
        "size_relative_snapshot": size.get("runner_snapshot", {}),
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "split": "train_only_claim_synthesis",
            "test_usage": False,
            "validation_usage": False,
            "calibrated_probability_claim_allowed": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "claim_skeleton.json", claim)
    write_csv(args.output_dir / "evidence_table.csv", evidence)
    write_csv(args.output_dir / "family_route_table.csv", families)
    write_csv(args.output_dir / "reviewer_risk_table.csv", risks)
    write_csv(args.output_dir / "route_decision.csv", decisions)
    write_json(args.output_dir / "next_plan_contract.json", next_contract)
    (args.output_dir / "framework_skeleton.md").write_text(framework_skeleton(), encoding="utf-8")
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary, claim, evidence, decisions)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
