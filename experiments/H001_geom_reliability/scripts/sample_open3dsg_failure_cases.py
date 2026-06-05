#!/usr/bin/env python3
"""Sample representative H001 qualitative failure cases."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_failure_case_sample_v1"
STATUS_READY = "failure_case_sample_ready"
STATUS_BLOCKED = "blocked_failure_rows_missing"
DEFAULT_SOURCE_NAME = "Open3DSG"
DEFAULT_CASE_ID_PREFIX = "open3dsg_case"
DEFAULT_RECORD_TYPE = "open3dsg_qualitative_case_candidate"

TRANSITION_PRIORITY = {
    "demoted_out_of_top50": 0,
    "demoted_out_of_top100": 1,
    "promoted_into_top50": 2,
    "promoted_into_top100": 3,
    "stayed_in_topk": 4,
}

CATEGORY_PRIORITY = {
    "geometry_contradiction": 0,
    "semantic_and_geometry_failure": 1,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--failure-rows",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_cases"),
    )
    parser.add_argument("--limit", type=int, default=36)
    parser.add_argument("--per-bucket", type=int, default=1)
    parser.add_argument("--max-per-subgraph", type=int, default=2)
    parser.add_argument("--source-name", default=DEFAULT_SOURCE_NAME)
    parser.add_argument("--case-id-prefix", default=DEFAULT_CASE_ID_PREFIX)
    parser.add_argument("--record-type", default=DEFAULT_RECORD_TYPE)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_number"] = line_number
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def counter_payload(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def row_bucket(row: dict[str, Any]) -> tuple[str, str, str]:
    source = row.get("source_prediction", {})
    taxonomy = row.get("failure_taxonomy", {})
    rerank = row.get("rerank_effect", {})
    return (
        str(taxonomy.get("primary_category")),
        str(source.get("predicate_family")),
        str(rerank.get("topk_transition")),
    )


def priority_key(row: dict[str, Any]) -> tuple[float, float, float, int, str]:
    source = row.get("source_prediction", {})
    geometry = row.get("geometry", {})
    rerank = row.get("rerank_effect", {})
    delta_rank = rerank.get("delta_rank")
    semantic_score = source.get("semantic_score")
    p_geom_valid = geometry.get("p_geom_valid")
    try:
        rank_signal = abs(float(delta_rank))
    except (TypeError, ValueError):
        rank_signal = 0.0
    try:
        semantic_signal = float(semantic_score)
    except (TypeError, ValueError):
        semantic_signal = 0.0
    try:
        geom_invalid_signal = 1.0 - float(p_geom_valid)
    except (TypeError, ValueError):
        geom_invalid_signal = 0.0
    return (
        -rank_signal,
        -semantic_signal,
        -geom_invalid_signal,
        int(row.get("_line_number", 0)),
        str(row.get("analysis_id", "")),
    )


def bucket_order_key(bucket: tuple[str, str, str]) -> tuple[int, str, int]:
    category, family, transition = bucket
    return (
        CATEGORY_PRIORITY.get(category, 99),
        family,
        TRANSITION_PRIORITY.get(transition, 99),
    )


def is_candidate(row: dict[str, Any]) -> bool:
    taxonomy = row.get("failure_taxonomy", {})
    audit_hooks = row.get("audit_hooks", {})
    return (
        bool(audit_hooks.get("needs_visual_audit"))
        and taxonomy.get("severity") == "high"
        and taxonomy.get("primary_category") in CATEGORY_PRIORITY
    )


def compact_case(
    row: dict[str, Any],
    case_index: int,
    *,
    record_type: str,
    case_id_prefix: str,
) -> dict[str, Any]:
    source = row.get("source_prediction", {})
    taxonomy = row.get("failure_taxonomy", {})
    geometry = row.get("geometry", {})
    gt = row.get("ground_truth", {})
    rerank = row.get("rerank_effect", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "case_id": f"{case_id_prefix}_{case_index:03d}",
        "source_analysis_id": row.get("analysis_id"),
        "source_line_number": row.get("_line_number"),
        "selection_bucket": {
            "primary_category": taxonomy.get("primary_category"),
            "predicate_family": source.get("predicate_family"),
            "topk_transition": rerank.get("topk_transition"),
        },
        "failure_taxonomy": {
            "primary_category": taxonomy.get("primary_category"),
            "secondary_categories": taxonomy.get("secondary_categories", []),
            "severity": taxonomy.get("severity"),
            "assignment_rule": taxonomy.get("assignment_rule"),
            "claim_use": taxonomy.get("claim_use"),
        },
        "source_prediction": {
            "scan_id": source.get("scan_id"),
            "subgraph_id": source.get("subgraph_id"),
            "subject_id": source.get("subject_id"),
            "subject_label": source.get("subject_label"),
            "object_id": source.get("object_id"),
            "object_label": source.get("object_label"),
            "predicate_label": source.get("predicate_label"),
            "predicate_family": source.get("predicate_family"),
            "semantic_score": source.get("semantic_score"),
            "semantic_rank_in_subgraph": source.get("semantic_rank_in_subgraph"),
            "predicate_rank_for_pair": source.get("predicate_rank_for_pair"),
            "topk_membership": source.get("topk_membership"),
        },
        "geometry": {
            "verification_status": geometry.get("verification_status"),
            "consistency_score": geometry.get("consistency_score"),
            "p_geom_valid": geometry.get("p_geom_valid"),
            "reason_codes": geometry.get("reason_codes", []),
            "geometry_source": geometry.get("geometry_source"),
        },
        "ground_truth": {
            "match_status": gt.get("match_status"),
            "matched_predicates": gt.get("matched_predicates", []),
            "matched_gt_ids": gt.get("matched_gt_ids", []),
        },
        "rerank_effect": {
            "condition": rerank.get("condition"),
            "semantic_rank": rerank.get("semantic_rank"),
            "geometry_rank": rerank.get("geometry_rank"),
            "delta_rank": rerank.get("delta_rank"),
            "topk_transition": rerank.get("topk_transition"),
        },
        "audit_hooks": {
            "needs_visual_audit": row.get("audit_hooks", {}).get("needs_visual_audit"),
            "suggested_check": suggested_check(row),
        },
    }


def suggested_check(row: dict[str, Any]) -> str:
    category = row.get("failure_taxonomy", {}).get("primary_category")
    geometry = row.get("geometry", {})
    reason_codes = ", ".join(geometry.get("reason_codes", []))
    if category == "geometry_contradiction":
        return f"Inspect whether the predicted relation is physically contradicted by the pair geometry; reason_codes={reason_codes}"
    return f"Inspect whether both semantic label and geometry evidence fail for this relation; reason_codes={reason_codes}"


def build_report(payload: dict[str, Any], cases: list[dict[str, Any]], repo_root: Path, *, source_name: str) -> str:
    lines = [
        f"# {source_name} Qualitative Failure Case Sample",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Scope",
        "",
        f"This sample is selected from high-severity {source_name} failure-analysis rows with `needs_visual_audit=true`.",
        "It is a qualitative inspection queue, not an additional metric.",
        "",
        "## Summary",
        "",
        f"- selected cases: `{payload['selected_count']}`",
        f"- candidate rows: `{payload['candidate_count']}`",
        f"- source rows: `{payload['source_row_count']}`",
        "",
        "## Selected Counts",
        "",
    ]
    for title, key in [
        ("By Category", "selected_by_category"),
        ("By Predicate Family", "selected_by_family"),
        ("By Top-k Transition", "selected_by_transition"),
    ]:
        lines.append(f"### {title}")
        lines.append("")
        for name, count in payload[key].items():
            lines.append(f"- `{name}`: {count}")
        lines.append("")
    lines.extend(["## First Cases", ""])
    lines.append("| case | category | family | predicate | pair | transition | delta |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for case in cases[:20]:
        source = case["source_prediction"]
        taxonomy = case["failure_taxonomy"]
        rerank = case["rerank_effect"]
        pair = f"{source.get('subject_label')} -> {source.get('object_label')}"
        lines.append(
            f"| `{case['case_id']}` | `{taxonomy.get('primary_category')}` | "
            f"`{source.get('predicate_family')}` | `{source.get('predicate_label')}` | "
            f"{pair} | `{rerank.get('topk_transition')}` | `{rerank.get('delta_rank')}` |"
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `queue_jsonl`: `{relpath(repo_root, Path(payload['outputs']['queue_jsonl']))}`",
            f"- `manifest_json`: `{relpath(repo_root, Path(payload['outputs']['manifest_json']))}`",
            f"- `report_md`: `{relpath(repo_root, Path(payload['outputs']['report_md']))}`",
            "",
            "## Claim Boundary",
            "",
            "Use these cases to choose visual examples and write failure narratives.",
            "Do not report them as a statistically representative audit without a separate labeling protocol.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root
    rows_path = resolve(repo_root, args.failure_rows)
    out_dir = resolve(repo_root, args.out)
    queue_path = out_dir / "queue.jsonl"
    manifest_path = out_dir / "manifest.json"
    report_path = out_dir / "report.md"

    if not rows_path.is_file():
        payload = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_BLOCKED,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "blockers": [f"missing_failure_rows:{relpath(repo_root, rows_path)}"],
            "outputs": {
                "queue_jsonl": str(queue_path),
                "manifest_json": str(manifest_path),
                "report_md": str(report_path),
            },
        }
        write_json(manifest_path, payload)
        report_path.write_text(
            f"# {args.source_name} Qualitative Failure Case Sample\n\nStatus: `blocked_failure_rows_missing`\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": STATUS_BLOCKED, "manifest": relpath(repo_root, manifest_path)}, sort_keys=True))
        return

    rows = read_jsonl(rows_path)
    candidates = [row for row in rows if is_candidate(row)]
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        buckets[row_bucket(row)].append(row)
    for bucket_rows in buckets.values():
        bucket_rows.sort(key=priority_key)

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    per_subgraph: Counter[str] = Counter()

    def try_add(row: dict[str, Any]) -> bool:
        analysis_id = str(row.get("analysis_id"))
        subgraph_id = str(row.get("source_prediction", {}).get("subgraph_id"))
        if analysis_id in selected_ids:
            return False
        if per_subgraph[subgraph_id] >= args.max_per_subgraph:
            return False
        selected.append(row)
        selected_ids.add(analysis_id)
        per_subgraph[subgraph_id] += 1
        return True

    for bucket in sorted(buckets, key=bucket_order_key):
        taken = 0
        for row in buckets[bucket]:
            if try_add(row):
                taken += 1
            if taken >= args.per_bucket or len(selected) >= args.limit:
                break
        if len(selected) >= args.limit:
            break

    if len(selected) < args.limit:
        remaining = sorted(candidates, key=priority_key)
        for row in remaining:
            try_add(row)
            if len(selected) >= args.limit:
                break

    cases = [
        compact_case(
            row,
            index + 1,
            record_type=args.record_type,
            case_id_prefix=args.case_id_prefix,
        )
        for index, row in enumerate(selected)
    ]
    selected_category = Counter(case["failure_taxonomy"]["primary_category"] for case in cases)
    selected_family = Counter(case["source_prediction"]["predicate_family"] for case in cases)
    selected_transition = Counter(case["rerank_effect"]["topk_transition"] for case in cases)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_rows": relpath(repo_root, rows_path),
        "source_row_count": len(rows),
        "candidate_count": len(candidates),
        "selected_count": len(cases),
        "selection_config": {
            "limit": args.limit,
            "per_bucket": args.per_bucket,
            "max_per_subgraph": args.max_per_subgraph,
            "source_name": args.source_name,
            "case_id_prefix": args.case_id_prefix,
            "record_type": args.record_type,
            "candidate_filter": "needs_visual_audit=true AND severity=high AND category in {geometry_contradiction, semantic_and_geometry_failure}",
            "bucket_key": ["primary_category", "predicate_family", "topk_transition"],
        },
        "candidate_by_category": counter_payload(Counter(row["failure_taxonomy"]["primary_category"] for row in candidates)),
        "selected_by_category": counter_payload(selected_category),
        "selected_by_family": counter_payload(selected_family),
        "selected_by_transition": counter_payload(selected_transition),
        "validation": {
            "all_selected_need_visual_audit": all(case["audit_hooks"]["needs_visual_audit"] for case in cases),
            "all_selected_high_severity": all(case["failure_taxonomy"]["severity"] == "high" for case in cases),
            "unique_source_analysis_ids": len({case["source_analysis_id"] for case in cases}) == len(cases),
        },
        "outputs": {
            "queue_jsonl": str(queue_path),
            "manifest_json": str(manifest_path),
            "report_md": str(report_path),
        },
        "claim_boundary": "qualitative inspection queue only; not a new metric or representative human audit",
    }

    write_jsonl(queue_path, cases)
    write_json(manifest_path, manifest)
    report_path.write_text(build_report(manifest, cases, repo_root, source_name=args.source_name), encoding="utf-8")
    print(json.dumps({"status": STATUS_READY, "selected_count": len(cases), "manifest": relpath(repo_root, manifest_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
