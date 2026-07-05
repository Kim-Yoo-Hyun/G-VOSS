#!/usr/bin/env python3
"""Update H002 multi-family synthesis after relative-horizontal result review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PREV_SYNTHESIS_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative"
DEFAULT_REL_H_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner"
DEFAULT_SIZE_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner"
DEFAULT_SUPPORT_REVIEW_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
)
DEFAULT_CLOSE_BY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal"

EXPECTED_PREV_STATUS = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_ready"
EXPECTED_REL_H_STATUS = (
    "h002_compatibility_dataset_v3_relative_horizontal_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update"
)
EXPECTED_REL_H_NEXT = "compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal"
EXPECTED_SIZE_STATUS = (
    "h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update"
)
EXPECTED_SUPPORT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis"
)
EXPECTED_CLOSE_BY_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_v1"
STATUS_READY = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_input_errors"
SELECTED_PATH = "update_relation_aware_compatibility_routing_claim_with_relative_horizontal_select_table_plan_update"
NEXT_TODO = "compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-synthesis-dir", type=Path, default=DEFAULT_PREV_SYNTHESIS_DIR)
    parser.add_argument("--relative-horizontal-review-dir", type=Path, default=DEFAULT_REL_H_REVIEW_DIR)
    parser.add_argument("--size-review-dir", type=Path, default=DEFAULT_SIZE_REVIEW_DIR)
    parser.add_argument("--support-review-dir", type=Path, default=DEFAULT_SUPPORT_REVIEW_DIR)
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
    previous: dict[str, Any],
    rel_h: dict[str, Any],
    size: dict[str, Any],
    support: dict[str, Any],
    close_by: dict[str, Any],
    previous_routes: list[dict[str, str]],
    rel_h_routes: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "previous_synthesis": (previous, EXPECTED_PREV_STATUS),
        "relative_horizontal_review": (rel_h, EXPECTED_REL_H_STATUS),
        "size_review": (size, EXPECTED_SIZE_STATUS),
        "support_review": (support, EXPECTED_SUPPORT_STATUS),
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

    if rel_h.get("next_todo") != EXPECTED_REL_H_NEXT:
        errors.append({"input": "relative_horizontal_review", "error_type": "unexpected_next_todo", "actual": rel_h.get("next_todo")})

    prev_route = {row.get("family"): row for row in previous_routes}
    if prev_route.get("relative_horizontal", {}).get("decision") != "defer":
        errors.append({"input": "previous_routes", "error_type": "relative_horizontal_was_not_previously_deferred"})

    rel_h_route = {row.get("relation_family"): row for row in rel_h_routes}
    if rel_h_route.get("relative_horizontal", {}).get("route_role") != "main_compatibility_route_mechanism_evidence_with_reference_frame_caveat":
        errors.append({"input": "relative_horizontal_routes", "error_type": "relative_horizontal_not_promoted_in_review"})

    snapshot = rel_h.get("runner_snapshot", {})
    numeric_gates = {
        "primary_auroc": (snapshot.get("primary_auroc"), 0.95, "min"),
        "semantic_only_auroc": (snapshot.get("semantic_only_auroc"), 0.60, "max"),
        "geometry_only_auroc": (snapshot.get("geometry_only_auroc"), 0.60, "max"),
        "concat_auroc": (snapshot.get("concat_auroc"), 0.60, "max"),
        "wrong_t_auroc": (snapshot.get("wrong_t_auroc"), 0.60, "max"),
        "shuffled_g_global_auroc": (snapshot.get("shuffled_g_global_auroc"), 0.60, "max"),
        "shuffled_g_within_predicate_auroc": (snapshot.get("shuffled_g_within_predicate_auroc"), 0.60, "max"),
        "wrong_frame_xy_swap_auroc": (snapshot.get("wrong_frame_xy_swap_auroc"), 0.60, "max"),
        "subject_object_swap_auroc": (snapshot.get("subject_object_swap_auroc"), 0.60, "max"),
    }
    for key, (value, threshold, direction) in numeric_gates.items():
        if value is None:
            errors.append({"input": "relative_horizontal_review", "error_type": "missing_snapshot_metric", "metric": key})
            continue
        value_f = float(value)
        if direction == "min" and value_f < threshold:
            errors.append({"input": "relative_horizontal_review", "error_type": "metric_below_threshold", "metric": key, "actual": value})
        if direction == "max" and value_f > threshold:
            errors.append({"input": "relative_horizontal_review", "error_type": "metric_above_threshold", "metric": key, "actual": value})
    if rel_h.get("boundary", {}).get("in_front_of_used") is not False:
        errors.append({"input": "relative_horizontal_review", "error_type": "in_front_of_boundary_not_false"})
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
            "Relative-vertical, size-relative, and frame-aware relative-horizontal families provide clean "
            "predicate-conditioned geometry compatibility evidence; support/contact provides a challenging "
            "compatibility route with caveat; proximity is a geometry-easy control; and attachment-like "
            "relations remain observability-heavy."
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
            "H002 currently supports a train-only mechanism claim: different relation families require "
            "different evidence routes, and explicit T_e x G_e compatibility is necessary in clean "
            "vertical, size, and frame-aware horizontal families while remaining useful but harder in support/contact."
        ),
        "blocked_claims": [
            "paper-level performance",
            "held-out/test relation reliability",
            "all relation-family generality",
            "complete horizontal ontology coverage including in front of",
            "support/contact fully solved",
            "Q_e as relation truth",
            "final calibrated p_rel/p_obs results",
            "geometry-only reliability framework",
        ],
    }


def rel_h_evidence_row(rel_h: dict[str, Any]) -> dict[str, Any]:
    s = rel_h["runner_snapshot"]
    return {
        "family": "relative_horizontal",
        "predicates": "left; right; front; behind",
        "route_type": "frame-aware clean compatibility mechanism",
        "primary_signal": f"{s['primary_auroc']:.6f}",
        "semantic_only": f"{s['semantic_only_auroc']:.6f}",
        "geometry_only": f"{s['geometry_only_auroc']:.6f}",
        "plain_concat": f"{s['concat_auroc']:.6f}",
        "wrong_T": f"{s['wrong_t_auroc']:.6f}",
        "shuffled_G": f"{s['shuffled_g_global_auroc']:.6f} / {s['shuffled_g_within_predicate_auroc']:.6f}",
        "paper_role": "main mechanism evidence with reference-frame caveat",
        "caveat": "frame-aware route only; in front of absent/excluded; not calibrated probability",
    }


def evidence_table(previous: list[dict[str, str]], rel_h: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inserted = False
    for row in previous:
        if row.get("family") == "relative_horizontal":
            rows.append(rel_h_evidence_row(rel_h))
            inserted = True
        else:
            rows.append(dict(row))
            if row.get("family") == "size_relative":
                rows.append(rel_h_evidence_row(rel_h))
                inserted = True
    if not inserted:
        rows.append(rel_h_evidence_row(rel_h))
    return rows


def family_route_table(previous: list[dict[str, str]]) -> list[dict[str, Any]]:
    replacement = {
        "family": "relative_horizontal",
        "route": "frame-aware clean compatibility mechanism",
        "predicates": "left; right; front; behind",
        "use_in_claim": "main_with_reference_frame_caveat",
        "evidence_route": "T_e x signed horizontal-axis G_e under frozen frame convention",
        "p_obs_role": "reference-frame and axis-boundary rows remain Q_e/diagnostic",
        "risk": "frame ambiguity and in-front-of absence",
        "decision": "promote as frame-aware main mechanism evidence; exclude in front of",
    }
    rows: list[dict[str, Any]] = []
    replaced = False
    for row in previous:
        if row.get("family") == "relative_horizontal":
            rows.append(replacement)
            replaced = True
        else:
            rows.append(dict(row))
    if not replaced:
        rows.append(replacement)
    order = {
        "relative_vertical": 0,
        "size_relative": 1,
        "relative_horizontal": 2,
        "support_contact": 3,
        "support_contact_superordinate": 4,
        "proximity": 5,
        "attachment_like": 6,
    }
    return sorted(rows, key=lambda row: order.get(str(row.get("family")), 99))


def reviewer_risks(previous: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [dict(row) for row in previous]
    rows.extend(
        [
            {
                "risk": "relative_horizontal requires a reference frame",
                "severity": "high_if_hidden",
                "answer": (
                    "State the frozen frame convention explicitly and include wrong-frame x/y-swap, sign-flip, "
                    "and endpoint-swap controls. Treat the route as frame-aware mechanism evidence only."
                ),
                "needed_artifact": "relative-horizontal result review and updated route table",
            },
            {
                "risk": "horizontal family is incomplete without in front of",
                "severity": "medium",
                "answer": (
                    "`in front of` is absent in the current train-side source and excluded from this claim. "
                    "Do not call this complete horizontal-spatial coverage."
                ),
                "needed_artifact": "claim boundary table with in-front-of exclusion",
            },
            {
                "risk": "clean vertical, size, and horizontal routes look rule-based",
                "severity": "medium",
                "answer": (
                    "Use the clean routes to prove the mechanism and pair them with support/contact as the challenging route. "
                    "The method claim is evidence routing and compatibility separation, not a single hand-written rule set."
                ),
                "needed_artifact": "multi-family evidence table and support/contact caveat",
            },
        ]
    )
    return rows


def route_decisions() -> list[dict[str, Any]]:
    return [
        {
            "route": "update_relation_aware_compatibility_routing_claim_with_relative_horizontal",
            "verdict": "selected",
            "reason": "relative_horizontal adds a frame-sensitive compatibility route beyond vertical and size clean routes.",
            "next_action": "update table/ablation plan to include relative_horizontal",
        },
        {
            "route": "claim_complete_horizontal_spatial_coverage",
            "verdict": "reject",
            "reason": "`in front of` is absent and frame convention remains a claim caveat.",
            "next_action": "keep horizontal ontology coverage blocked",
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
            "reason": "relative_horizontal geometry-only AUROC is chance; the evidence supports predicate-conditioned frame-aware compatibility.",
            "next_action": "keep T_e x G_e controls central",
        },
        {
            "route": "ablation_and_table_plan_update_after_relative_horizontal",
            "verdict": "selected_next",
            "reason": "the current table plan predates the relative-horizontal promotion.",
            "next_action": NEXT_TODO,
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Update the H002 table and ablation contract after adding relative_horizontal to the multi-family route synthesis.",
        "must_include": [
            "relative_vertical clean compatibility row",
            "size_relative clean compatibility row",
            "relative_horizontal frame-aware compatibility row",
            "support_contact challenging compatibility row with caveat",
            "proximity geometry-easy diagnostic/control row",
            "attachment_like observability-heavy deferred row",
            "semantic-only, geometry-only, no-interaction concat, T_e x G_e interaction, wrong-T, shuffled-G, sign-flip controls where applicable",
            "wrong-frame and endpoint-swap controls for relative_horizontal",
            "calibration caveat for high-AUROC but high-ECE smoke results",
        ],
        "must_not_do": [
            "do not promote to paper-level result",
            "do not claim calibrated p_rel or p_obs",
            "do not claim complete horizontal relation ontology",
            "do not treat Q_e as relation truth",
            "do not hide support/contact near-threshold caveat",
            "do not call clean vertical/size/horizontal routes universal relation generalization",
        ],
    }


def framework_skeleton() -> str:
    return """# H002 Framework Skeleton After Relative-Horizontal Synthesis

## Working Title

Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations

## Core Thesis

Relation reliability should not be estimated by a fixed semantic-geometry score
fusion. H002 represents relation edges through separated factors and routes each
relation family through the evidence path that is meaningful for that family.

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

- `relative_vertical`: clean sign compatibility route.
- `size_relative`: clean size-comparison compatibility route.
- `relative_horizontal`: frame-aware directional compatibility route.
- `support_contact`: challenging compatibility route with point/contact/pose evidence.
- `proximity`: geometry-easy control under the current `close by` target.
- `attachment_like`: observability-heavy future/deferred route.

## Allowed Claim

H002 currently supports a train-only mechanism claim: relation families require
different evidence routes, and explicit `T_e x G_e` compatibility is necessary in
clean vertical, size, and frame-aware horizontal families while remaining useful
but harder in support/contact relations.

## Blocked Claims

- paper-level performance
- held-out/test reliability
- calibrated `p_rel` / `p_obs`
- complete horizontal ontology coverage including `in front of`
- universal all-family generality
- support/contact fully solved
- geometry-only relation reliability
"""


def write_report(
    path: Path,
    summary: dict[str, Any],
    claim: dict[str, Any],
    evidence: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> None:
    lines = [
        "# Multi-Family Claim Synthesis After Relative-Horizontal",
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
    for row in decisions:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "`relative_horizontal` strengthens H002 by adding a frame-aware route: the same",
            "horizontal geometry must be interpreted through predicate semantics and a fixed",
            "reference-frame convention. It does not make H002 a geometry-only method, because",
            "geometry-only and no-interaction concat remain near chance.",
            "",
            "The next step is to update the ablation/table plan so the route map and controls",
            "include the horizontal wrong-frame and endpoint-swap checks.",
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
    previous_evidence = read_csv(args.previous_synthesis_dir / "evidence_table.csv")
    previous_routes = read_csv(args.previous_synthesis_dir / "family_route_table.csv")
    previous_risks = read_csv(args.previous_synthesis_dir / "reviewer_risk_table.csv")
    rel_h = read_json(args.relative_horizontal_review_dir / "summary.json")
    rel_h_routes = read_csv(args.relative_horizontal_review_dir / "route_position.csv")
    size = read_json(args.size_review_dir / "summary.json")
    support = read_json(args.support_review_dir / "summary.json")
    close_by = read_json(args.close_by_dir / "summary.json")

    roots = {
        "previous_synthesis": args.previous_synthesis_dir,
        "relative_horizontal_review": args.relative_horizontal_review_dir,
        "size_review": args.size_review_dir,
        "support_review": args.support_review_dir,
        "close_by": args.close_by_dir,
    }
    errors = validate_inputs(previous, rel_h, size, support, close_by, previous_routes, rel_h_routes, roots)

    claim = claim_skeleton()
    evidence = evidence_table(previous_evidence, rel_h)
    family_routes = family_route_table(previous_routes)
    risks = reviewer_risks(previous_risks)
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
            "relative_horizontal_review": rel_path(args.relative_horizontal_review_dir),
            "size_review": rel_path(args.size_review_dir),
            "support_review": rel_path(args.support_review_dir),
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
            "family_route_rows": len(family_routes),
            "reviewer_risk_rows": len(risks),
            "route_decision_rows": len(decisions),
        },
        "claim_boundary": claim,
        "relative_horizontal_snapshot": rel_h.get("runner_snapshot", {}),
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "split": "train_only_claim_synthesis",
            "test_usage": False,
            "validation_usage": False,
            "calibrated_probability_claim_allowed": False,
            "complete_horizontal_ontology_claim_allowed": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "claim_skeleton.json", claim)
    write_csv(args.output_dir / "evidence_table.csv", evidence)
    write_csv(args.output_dir / "family_route_table.csv", family_routes)
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
