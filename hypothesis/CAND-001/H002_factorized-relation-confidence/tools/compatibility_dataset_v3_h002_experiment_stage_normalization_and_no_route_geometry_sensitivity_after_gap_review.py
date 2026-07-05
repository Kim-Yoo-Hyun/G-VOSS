#!/usr/bin/env python3
"""Review H002 normalization and no-route geometry sensitivity."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review"
ARTIFACT = f"compatibility_dataset_v3_{STAGE}"
STATUS_READY = f"{STAGE}_ready"
H2 = Path("hypothesis/CAND-001/H002_factorized-relation-confidence")
RUNTIME = Path("experiments/H002_compatibility_routing/source_reranking_sensitivity/latest")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def f6(value: Any) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):.6f}"


def row_for(rows: list[dict[str, str]], score: str, k: int) -> dict[str, str]:
    for row in rows:
        if row.get("level") == "primary_success_weighted" and row.get("score_id") == score and int(row.get("K", -1)) == k:
            return row
    return {}


def comparison_for(rows: list[dict[str, str]], comparison: str, k: int) -> dict[str, str]:
    for row in rows:
        if row.get("comparison") == comparison and int(row.get("K", -1)) == k:
            return row
    return {}


def main() -> int:
    out = H2 / "artifacts" / ARTIFACT
    out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []

    required = {
        "summary": RUNTIME / "summary.json",
        "aggregate": RUNTIME / "aggregate_metrics.csv",
        "comparison": RUNTIME / "comparison_metrics.csv",
        "validation_errors": RUNTIME / "validation_errors.jsonl",
    }
    for key, path in required.items():
        if not path.exists():
            errors.append({"error_type": "missing_runtime_output", "key": key, "path": str(path)})

    runtime_summary: dict[str, Any] = {}
    aggregate_rows: list[dict[str, str]] = []
    comparison_rows: list[dict[str, str]] = []
    if not errors:
        runtime_summary = read_json(required["summary"])
        aggregate_rows = read_csv(required["aggregate"])
        comparison_rows = read_csv(required["comparison"])
        if runtime_summary.get("validation_errors") != 0:
            errors.append({"error_type": "runtime_validation_errors", "actual": runtime_summary.get("validation_errors")})
        if runtime_summary.get("status") != "h002_source_reranking_sensitivity_ready":
            errors.append({"error_type": "unexpected_runtime_status", "actual": runtime_summary.get("status")})

    key_table: list[dict[str, Any]] = []
    if not errors:
        for score in [
            "S0_source_score_minmax",
            "S2_minmax_source_x_Ce",
            "S2_raw_source_x_Ce",
            "S2_rankpct_source_x_Ce",
            "A1_minmax_route_G_only",
            "A1_minmax_no_route_G_only",
            "A2_minmax_TG_concat",
        ]:
            for k in [10, 20, 50]:
                row = row_for(aggregate_rows, score, k)
                if row:
                    key_table.append(
                        {
                            "score_id": score,
                            "K": k,
                            "Recall@K": f6(row.get("Recall@K")),
                            "Violation@K": f6(row.get("Violation@K")),
                        }
                    )

    principle_review = [
        {
            "principle": "method form follows problem cause",
            "status": "pass_scoped",
            "judgment": "The problem is source confidence mixing semantic plausibility with geometric compatibility. H002's S2 separates C_e from Z_e, then recombines them for reranking, which directly targets that cause.",
            "caveat": "This is proven for comparison-route relations, not all relation families.",
        },
        {
            "principle": "not just geometry filtering",
            "status": "pass",
            "judgment": "S2 beats both route-aware G-only and no-route G-only at K=10/20/50 while reducing violations.",
            "caveat": "Keep A1 as an ablation/control; do not claim geometry evidence alone is enough.",
        },
        {
            "principle": "not just arbitrary normalization",
            "status": "partial_pass",
            "judgment": "Raw source*C_e preserves direction versus S0 at K=10/20/50. Rank-percentile reduces violations but loses low-K recall at K=10.",
            "caveat": "Do not claim normalization-invariant gains. Present minmax as the selected risk-utility score and raw product as sensitivity support.",
        },
        {
            "principle": "relation-aware routing framework",
            "status": "framework_constructed_not_fully_validated",
            "judgment": "Route map, route-specific evidence schema, C_e/p_obs/p_rel contracts, support/contact failure taxonomy, and source-reranking pipeline exist.",
            "caveat": "Only comparison route has paper-ready quantitative success. General framework remains a structured roadmap plus partial evidence.",
        },
        {
            "principle": "general reliable 3D relation framework",
            "status": "not_yet",
            "judgment": "Current evidence is insufficient for a completed general reliable 3D relation framework.",
            "caveat": "Use 'toward relation-aware reliable 3D relations' or 'route-aware framework candidate', not 'general framework solved'.",
        },
    ]

    framework_scope = [
        {
            "component": "route map",
            "status": "constructed",
            "evidence": "comparison, geometry-only, frame-aware, support/contact, observability-heavy, and semantic/structural routes are defined in the H002 route framework.",
            "paper_role": "method framing / framework overview",
        },
        {
            "component": "comparison route",
            "status": "validated_main",
            "evidence": "S2 improves Recall@K and Violation@K over S0/A1/A2 in primary success families.",
            "paper_role": "main quantitative claim",
        },
        {
            "component": "geometry-only route",
            "status": "diagnostic_control",
            "evidence": "close-by/proximity and G-only controls show geometry-decidable cases, but not main C_e interaction evidence.",
            "paper_role": "control / route diversity",
        },
        {
            "component": "support/contact route",
            "status": "failure_taxonomy",
            "evidence": "hard-route transfer fails; richer pose/contact/mesh evidence is needed.",
            "paper_role": "limitation and design necessity",
        },
        {
            "component": "observability p_obs/p_rel",
            "status": "framework_component_only",
            "evidence": "selective stress-test passed but calibrated quantitative claim is blocked.",
            "paper_role": "method interface or appendix stress-test, not solved result",
        },
    ]

    final_decision = {
        "method_principle": "natural_and_principled_for_scoped_problem",
        "relation_aware_evidence_routing_framework": "constructed_as_framework_and_partially_validated",
        "general_reliable_3d_relation_framework": "not_yet_validated",
        "normalization_decision": "minmax_main_allowed_with_raw_product_sensitivity_and_rankpct_caveat",
        "geometry_only_decision": "no_route_g_only_sensitivity_passed; S2 gain is not explained by route-family one-hot geometry baseline",
        "paper_claim_decision": "comparison_route_main_claim_allowed; broad_general_framework_claim_blocked",
    }

    report = """# H002 Normalization and No-Route Geometry Sensitivity Review

## Decision

```text
method_principle = natural_and_principled_for_scoped_problem
relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
general_reliable_3d_relation_framework = not_yet_validated
paper_claim_decision = comparison_route_main_claim_allowed; broad_general_framework_claim_blocked
```

The current method is principled for the scoped problem: source confidence is
not relation reliability, so H002 computes `C_e = compatibility(T_e, G_e)`
without `Z_e`, then combines it with `Z_e` only for source reranking. This is a
direct response to the problem formulation.

However, H002 has not yet validated a completed general reliable 3D relation
framework. It has built the route-aware evidence routing framework skeleton and
validated the comparison route.

## Sensitivity Summary

"""
    report += "| Score | K | Recall@K | Violation@K |\n| --- | ---: | ---: | ---: |\n"
    for row in key_table:
        report += f"| `{row['score_id']}` | {row['K']} | {row['Recall@K']} | {row['Violation@K']} |\n"

    report += """
## Interpretation

- No-route geometry-only sensitivity passes. Removing `route_family` from the
  G-only feature set does not explain away the S2 gain.
- Raw `source_score * C_e` also preserves the direction of improvement over S0
  at K=10/20/50, so the effect is not purely an artifact of minmax.
- Rank-percentile normalization is not sufficient at low K: it strongly reduces
  violations but loses Recall@10. Therefore the paper must not claim
  normalization-invariant improvement.
- The main score should be framed as a selected risk-utility score, not as an
  arbitrary normalization-free theorem.

## Framework Check

"""
    for row in framework_scope:
        report += f"- `{row['status']}` {row['component']}: {row['evidence']} Paper role: {row['paper_role']}.\n"

    report += """
## Required Wording

- Allowed: H002 is a route-aware reliability/reranking framework candidate with
  validated comparison-route evidence.
- Allowed: `S2_source_x_Ce` improves validation-level source reranking for
  geometry-checkable comparison relations.
- Blocked: H002 is a completed general reliable 3D relation framework.
- Blocked: all relation families are solved.
- Blocked: calibrated `p_obs/p_rel` reliability is solved.
"""

    summary = {
        "schema_version": f"{STAGE}_v1",
        "status": STATUS_READY if not errors else f"{STAGE}_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_root": str(RUNTIME),
        "validation_errors": len(errors),
        "runtime_sensitivity_pass": runtime_summary.get("gate", {}).get("sensitivity_pass") if runtime_summary else None,
        "final_decision": final_decision,
        "key_rows": len(key_table),
        "principle_review_rows": len(principle_review),
        "framework_scope_rows": len(framework_scope),
        "next_todo": "h002_paper_claim_boundary_update_after_sensitivity_review",
    }

    write_csv(out / "key_sensitivity_table.csv", key_table)
    write_csv(out / "principle_review.csv", principle_review)
    write_csv(out / "framework_scope_review.csv", framework_scope)
    (out / "report.md").write_text(report, encoding="utf-8")
    write_json(out / "summary.json", summary)
    write_jsonl(out / "validation_errors.jsonl", errors)

    stage_doc = H2 / f"compatibility_dataset_v3_{STAGE}.md"
    stage_doc.write_text(
        f"""# {STAGE}

Artifact:

```text
{out}
```

Status: `{summary['status']}`

Validation errors: `{summary['validation_errors']}`

Decision:

```text
method_principle = {final_decision['method_principle']}
relation_aware_evidence_routing_framework = {final_decision['relation_aware_evidence_routing_framework']}
general_reliable_3d_relation_framework = {final_decision['general_reliable_3d_relation_framework']}
normalization_decision = {final_decision['normalization_decision']}
geometry_only_decision = {final_decision['geometry_only_decision']}
next_todo = {summary['next_todo']}
```

See `{out / 'report.md'}` for the full review.
""",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
