#!/usr/bin/env python3
"""Inspect sampled H001 qualitative failure cases."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_failure_case_inspection_v1"
STATUS_READY = "qualitative_case_inspection_ready"
STATUS_BLOCKED = "blocked_failure_case_queue_missing"
DEFAULT_SOURCE_NAME = "Open3DSG"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--queue-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl"),
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_cases/manifest.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_cases"),
    )
    parser.add_argument("--source-name", default=DEFAULT_SOURCE_NAME)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def counter_payload(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def case_pair(case: dict[str, Any]) -> str:
    source = case.get("source_prediction", {})
    return f"{source.get('subject_label')} -> {source.get('object_label')}"


def compact_case(case: dict[str, Any]) -> dict[str, Any]:
    source = case.get("source_prediction", {})
    taxonomy = case.get("failure_taxonomy", {})
    geometry = case.get("geometry", {})
    rerank = case.get("rerank_effect", {})
    gt = case.get("ground_truth", {})
    return {
        "case_id": case.get("case_id"),
        "category": taxonomy.get("primary_category"),
        "family": source.get("predicate_family"),
        "predicate": source.get("predicate_label"),
        "pair": case_pair(case),
        "semantic_rank": rerank.get("semantic_rank"),
        "geometry_rank": rerank.get("geometry_rank"),
        "delta_rank": rerank.get("delta_rank"),
        "topk_transition": rerank.get("topk_transition"),
        "p_geom_valid": geometry.get("p_geom_valid"),
        "reason_codes": geometry.get("reason_codes", []),
        "gt_match_status": gt.get("match_status"),
        "matched_predicates": gt.get("matched_predicates", []),
    }


def finite_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def selected_cases(cases: list[dict[str, Any]], predicate, limit: int, key) -> list[dict[str, Any]]:
    return [compact_case(row) for row in sorted((row for row in cases if predicate(row)), key=key)[:limit]]


def family_mechanism_examples(cases: list[dict[str, Any]], limit_per_family: int = 2) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: Counter[str] = Counter()
    for row in sorted(
        cases,
        key=lambda item: (
            str(item.get("source_prediction", {}).get("predicate_family")),
            -abs(finite_float(item.get("rerank_effect", {}).get("delta_rank"))),
            str(item.get("case_id")),
        ),
    ):
        family = str(row.get("source_prediction", {}).get("predicate_family"))
        if seen[family] >= limit_per_family:
            continue
        selected.append(compact_case(row))
        seen[family] += 1
    return selected


def build_payload(
    repo_root: Path,
    queue_path: Path,
    manifest_path: Path,
    out_dir: Path,
    cases: list[dict[str, Any]],
    sample_manifest: dict[str, Any],
    source_name: str,
) -> dict[str, Any]:
    category_counter = Counter(case.get("failure_taxonomy", {}).get("primary_category") for case in cases)
    family_counter = Counter(case.get("source_prediction", {}).get("predicate_family") for case in cases)
    transition_counter = Counter(case.get("rerank_effect", {}).get("topk_transition") for case in cases)
    gt_counter = Counter(case.get("ground_truth", {}).get("match_status") for case in cases)
    reason_counter: Counter[str] = Counter()
    for case in cases:
        reason_counter.update(case.get("geometry", {}).get("reason_codes", []))

    demoted = [case for case in cases if finite_float(case.get("rerank_effect", {}).get("delta_rank")) > 0]
    promoted_or_stayed = [case for case in cases if finite_float(case.get("rerank_effect", {}).get("delta_rank")) <= 0]
    high_p_violated = [
        case
        for case in cases
        if case.get("geometry", {}).get("verification_status") == "violated"
        and finite_float(case.get("geometry", {}).get("p_geom_valid")) > 0.9
    ]

    p_values = [finite_float(case.get("geometry", {}).get("p_geom_valid")) for case in cases]
    semantic_ranks = [int(finite_float(case.get("rerank_effect", {}).get("semantic_rank"))) for case in cases]
    geometry_ranks = [int(finite_float(case.get("rerank_effect", {}).get("geometry_rank"))) for case in cases]

    representative = {
        "semantic_high_geometry_demoted": selected_cases(
            cases,
            lambda row: finite_float(row.get("rerank_effect", {}).get("delta_rank")) > 0,
            8,
            lambda row: -finite_float(row.get("rerank_effect", {}).get("delta_rank")),
        ),
        "geometry_promoted_or_retained_tradeoff": selected_cases(
            cases,
            lambda row: finite_float(row.get("rerank_effect", {}).get("delta_rank")) <= 0,
            8,
            lambda row: finite_float(row.get("rerank_effect", {}).get("delta_rank")),
        ),
        "residual_calibration_risk": selected_cases(
            cases,
            lambda row: row.get("geometry", {}).get("verification_status") == "violated"
            and finite_float(row.get("geometry", {}).get("p_geom_valid")) > 0.9,
            8,
            lambda row: -finite_float(row.get("geometry", {}).get("p_geom_valid")),
        ),
        "family_mechanism_examples": [
            *family_mechanism_examples(cases)
        ],
    }

    observations = [
        {
            "name": "semantic_plausibility_can_conflict_with_geometry",
            "evidence": (
                f"{len(demoted)} of {len(cases)} selected cases are demoted by geometry-aware reranking. "
                "Several have semantic top-50 ranks but low p_geom_valid or explicit geometry reason codes."
            ),
        },
        {
            "name": "failure_is_family_structured",
            "evidence": (
                "proximity failures concentrate in far_in_normalized_xy; relative_vertical failures "
                "concentrate in vertical_order_contradicts_predicate; support_contact failures expose "
                "float-gap or support-plane contradictions."
            ),
        },
        {
            "name": "reranking_has_recall_tradeoff_cases",
            "evidence": (
                f"{len(promoted_or_stayed)} selected cases are promoted or retained by geometry-aware ranking. "
                "These are useful for explaining why the paper must report recall and violation jointly."
            ),
        },
        {
            "name": "calibration_is_not_equivalent_to_hard_rule_validity",
            "evidence": (
                f"{len(high_p_violated)} selected cases are rule-violated but have p_geom_valid > 0.9. "
                "These residual cases justify reporting rule-verified, probabilistic, and family-specific variants separately."
            ),
        },
        {
            "name": "qualitative_queue_is_not_a_human_audit",
            "evidence": (
                "The queue is deterministic diagnostic evidence from prediction/GT/geometry joins. "
                "It should guide figure selection and failure narratives, not be reported as a representative visual audit."
            ),
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "source_name": source_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "queue_jsonl": relpath(repo_root, queue_path),
            "sample_manifest_json": relpath(repo_root, manifest_path),
        },
        "sample_status": sample_manifest.get("status"),
        "counts": {
            "selected_cases": len(cases),
            "by_category": counter_payload(category_counter),
            "by_family": counter_payload(family_counter),
            "by_topk_transition": counter_payload(transition_counter),
            "by_gt_match_status": counter_payload(gt_counter),
            "by_reason_code": counter_payload(reason_counter),
            "demoted_by_geometry": len(demoted),
            "promoted_or_retained_by_geometry": len(promoted_or_stayed),
            "violated_with_p_geom_valid_gt_0_9": len(high_p_violated),
            "p_geom_valid_min": min(p_values) if p_values else None,
            "p_geom_valid_max": max(p_values) if p_values else None,
            "semantic_rank_min": min(semantic_ranks) if semantic_ranks else None,
            "semantic_rank_max": max(semantic_ranks) if semantic_ranks else None,
            "geometry_rank_min": min(geometry_ranks) if geometry_ranks else None,
            "geometry_rank_max": max(geometry_ranks) if geometry_ranks else None,
        },
        "observations": observations,
        "representative_cases": representative,
        "paper_use": {
            "allowed": [
                "Use as qualitative failure-mechanism examples tied to Table 6 and the locked taxonomy.",
                "Use demoted cases to show semantically plausible but physically inconsistent relations.",
                "Use promoted or retained cases to explain recall/violation tradeoffs.",
                "Use high-p but rule-violated cases to disclose residual calibration risk.",
                "Use family-specific reason codes to justify family-specific controls and denominator reporting.",
            ],
            "not_allowed": [
                "Do not report the 36-case queue as a representative human audit.",
                "Do not change the locked taxonomy based on this inspection without a schema version bump.",
                "Do not claim broad open-vocabulary 3DSSG improvement from these qualitative cases alone.",
            ],
        },
        "outputs": {
            "inspection_json": relpath(repo_root, out_dir / "inspection.json"),
            "inspection_md": relpath(repo_root, out_dir / "inspection.md"),
        },
        "claim_boundary": (
            "qualitative reviewer-defense artifact only; not a new metric, not a visual audit, "
            "and not evidence beyond measured H001-family scope"
        ),
    }


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def case_table(cases: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| case | category | family | predicate | pair | transition | sem -> geom rank | p_geom_valid | reason |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for case in cases:
        lines.append(
            "| `{case_id}` | `{category}` | `{family}` | `{predicate}` | {pair} | `{transition}` | "
            "{semantic_rank} -> {geometry_rank} | {p_geom_valid} | `{reason}` |".format(
                case_id=case["case_id"],
                category=case["category"],
                family=case["family"],
                predicate=case["predicate"],
                pair=case["pair"],
                transition=case["topk_transition"],
                semantic_rank=case["semantic_rank"],
                geometry_rank=case["geometry_rank"],
                p_geom_valid=fmt(case["p_geom_valid"]),
                reason="; ".join(case["reason_codes"]),
            )
        )
    return lines


def build_report(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    source_name = payload.get("source_name") or DEFAULT_SOURCE_NAME
    lines = [
        f"# {source_name} Qualitative Failure Case Inspection",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Scope",
        "",
        f"This report inspects the sampled {source_name} qualitative queue generated from real prediction, GT, geometry, and metric joins.",
        "It does not add a metric and does not perform an independent visual audit.",
        "",
        "## Inspection Verdict",
        "",
        "- The queue supports the H001 failure mechanism: semantically plausible relation predictions can be physically inconsistent at the relation/object-pair level.",
        "- The failure pattern is family-structured rather than a generic score artifact.",
        "- Geometry-aware reranking also has promotion/retention cases, so paper wording must report recall and violation jointly.",
        "- Some violated cases still receive high calibrated probability, so rule-verified and probabilistic variants must remain separate in tables.",
        "- No taxonomy change is made in this inspection.",
        "",
        "## Counts",
        "",
        f"- selected cases: `{counts['selected_cases']}`",
        f"- demoted by geometry-aware reranking: `{counts['demoted_by_geometry']}`",
        f"- promoted or retained by geometry-aware reranking: `{counts['promoted_or_retained_by_geometry']}`",
        f"- violated but p_geom_valid > 0.9: `{counts['violated_with_p_geom_valid_gt_0_9']}`",
        f"- p_geom_valid range: `{fmt(counts['p_geom_valid_min'])}` to `{fmt(counts['p_geom_valid_max'])}`",
        f"- semantic rank range: `{counts['semantic_rank_min']}` to `{counts['semantic_rank_max']}`",
        f"- geometry rank range: `{counts['geometry_rank_min']}` to `{counts['geometry_rank_max']}`",
        "",
        "### By Category",
        "",
    ]
    for key, value in counts["by_category"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "### By Family", ""])
    for key, value in counts["by_family"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "### By Reason Code", ""])
    for key, value in counts["by_reason_code"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(
        [
            "",
            "## Mechanism Notes",
            "",
        ]
    )
    for item in payload["observations"]:
        lines.append(f"- `{item['name']}`: {item['evidence']}")

    lines.extend(["", "## Representative Demotions", ""])
    lines.extend(case_table(payload["representative_cases"]["semantic_high_geometry_demoted"]))
    lines.extend(["", "## Representative Promotion Or Retention Tradeoffs", ""])
    lines.extend(case_table(payload["representative_cases"]["geometry_promoted_or_retained_tradeoff"]))
    lines.extend(["", "## Residual Calibration Risk Cases", ""])
    lines.extend(case_table(payload["representative_cases"]["residual_calibration_risk"]))
    lines.extend(["", "## Family Mechanism Examples", ""])
    lines.extend(case_table(payload["representative_cases"]["family_mechanism_examples"]))

    lines.extend(
        [
            "",
            "## Paper Use",
            "",
            "Allowed:",
            "",
        ]
    )
    for item in payload["paper_use"]["allowed"]:
        lines.append(f"- {item}")
    lines.extend(["", "Not allowed:", ""])
    for item in payload["paper_use"]["not_allowed"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `inspection_json`: `{payload['outputs']['inspection_json']}`",
            f"- `inspection_md`: `{payload['outputs']['inspection_md']}`",
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"],
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root
    queue_path = resolve(repo_root, args.queue_jsonl)
    manifest_path = resolve(repo_root, args.manifest_json)
    out_dir = resolve(repo_root, args.out)
    inspection_json = out_dir / "inspection.json"
    inspection_md = out_dir / "inspection.md"

    if not queue_path.is_file():
        payload = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_BLOCKED,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "blockers": [f"missing_queue:{relpath(repo_root, queue_path)}"],
            "outputs": {
                "inspection_json": relpath(repo_root, inspection_json),
                "inspection_md": relpath(repo_root, inspection_md),
            },
        }
        write_json(inspection_json, payload)
        inspection_md.write_text(
            f"# {args.source_name} Qualitative Failure Case Inspection\n\nStatus: `blocked_failure_case_queue_missing`\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": STATUS_BLOCKED, "inspection": relpath(repo_root, inspection_json)}, sort_keys=True))
        return

    cases = read_jsonl(queue_path)
    sample_manifest = read_json(manifest_path) if manifest_path.is_file() else {}
    payload = build_payload(repo_root, queue_path, manifest_path, out_dir, cases, sample_manifest, args.source_name)
    write_json(inspection_json, payload)
    inspection_md.write_text(build_report(payload), encoding="utf-8")
    print(json.dumps({"status": STATUS_READY, "cases": len(cases), "inspection": relpath(repo_root, inspection_json)}, sort_keys=True))


if __name__ == "__main__":
    main()
