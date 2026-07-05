#!/usr/bin/env python3
"""Decide the next path after R7 attachment-observability schema audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_schema_shortcut_audit"
)
DEFAULT_MATERIALIZATION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_materialization"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_source_inventory"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_schema_shortcut_audit_blocked_shortcut_risk"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit"
EXPECTED_MATERIALIZATION_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_path_decision_select_class_pair_balanced_repair_mining"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_attachment_observability_path_decision_input_errors"
SELECTED_PATH = "attempt_one_class_pair_balanced_r7_repair_before_diagnostic_freeze"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan"

MIN_REPAIR_ROWS = 400
MIN_REPAIR_POSITIVE_ROWS = 100
MIN_EXACT_STRATA = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
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
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(
    audit_summary: dict[str, Any],
    materialization_summary: dict[str, Any],
    source_summary: dict[str, Any],
    audit_dir: Path,
    materialization_dir: Path,
    source_inventory_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("learned_smoke_allowed") is not False:
        errors.append({"error_type": "audit_unexpectedly_allows_smoke", "actual": audit_summary.get("learned_smoke_allowed")})
    counts = audit_summary.get("counts", {})
    if counts.get("schema_leakage_hits") != 0:
        errors.append({"error_type": "schema_leakage_not_zero", "actual": counts.get("schema_leakage_hits")})
    if counts.get("allowed_high_risk_blockers", 0) < 1:
        errors.append({"error_type": "missing_allowed_high_risk_blocker", "actual": counts.get("allowed_high_risk_blockers")})

    if materialization_summary.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append(
            {"error_type": "unexpected_materialization_status", "actual": materialization_summary.get("status")}
        )
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_status", "actual": source_summary.get("status")})

    for summary_name, summary in [
        ("audit", audit_summary),
        ("materialization", materialization_summary),
        ("source_inventory", source_summary),
    ]:
        boundary = summary.get("boundary", {})
        for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
            if boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": f"{summary_name}_boundary_not_false",
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )

    for name in ["summary.json", "critical_probe_failures.csv", "shortcut_probe_summary.csv"]:
        if not (audit_dir / name).exists():
            errors.append({"error_type": "missing_audit_artifact", "path": rel_path(audit_dir / name)})
    for name in ["model_safe_view.jsonl", "target_manifest.jsonl", "hidden_manifest.jsonl", "source_rows.jsonl"]:
        if not (materialization_dir / name).exists():
            errors.append({"error_type": "missing_materialization_artifact", "path": rel_path(materialization_dir / name)})
    for name in ["summary.json", "full_train_top_class_pairs.csv", "route_readiness.csv"]:
        if not (source_inventory_dir / name).exists():
            errors.append({"error_type": "missing_source_inventory_artifact", "path": rel_path(source_inventory_dir / name)})
    return errors


def target_rows(
    model_rows: list[dict[str, Any]],
    target_rows_: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (model, target) in enumerate(zip(model_rows, target_rows_)):
        rows.append(
            {
                "index": index,
                "p_obs": target.get("p_obs_target"),
                "p_rel": target.get("p_rel_observable_target"),
                "p_rel_usable": target.get("p_rel_observable_usable") is True,
                "predicate": model.get("t_predicate_label"),
                "q_visual_evidence_tier": model.get("q_visual_evidence_tier"),
                "rank_proxy_absent": True,
                "route_role": target.get("route_role"),
                "subject_object_pair": model.get("t_subject_object_pair"),
                "subject_object_family_pair": f"{model.get('t_subject_family')}|{model.get('t_object_family')}",
            }
        )
    return rows


def mixed_capacity(
    rows: list[dict[str, Any]],
    target_name: str,
    axis_name: str,
    axis_fn: Callable[[dict[str, Any]], Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        label = row[target_name]
        if label not in (0, 1):
            continue
        groups[str(axis_fn(row))][int(label)] += 1
    mixed = {key: count for key, count in groups.items() if count[0] > 0 and count[1] > 0}
    balanced_capacity = sum(2 * min(count[0], count[1]) for count in mixed.values())
    top: list[dict[str, Any]] = []
    for key, count in sorted(
        mixed.items(),
        key=lambda item: (min(item[1][0], item[1][1]), sum(item[1].values())),
        reverse=True,
    )[:30]:
        top.append(
            {
                "axis": axis_name,
                "balanced_capacity": 2 * min(count[0], count[1]),
                "negative": count[0],
                "positive": count[1],
                "stratum": key,
                "target": target_name,
                "total": sum(count.values()),
            }
        )
    summary = {
        "axis": axis_name,
        "balanced_capacity": balanced_capacity,
        "groups": len(groups),
        "mixed_groups": len(mixed),
        "negative_capacity": balanced_capacity // 2,
        "positive_capacity": balanced_capacity // 2,
        "target": target_name,
    }
    return summary, top


def current_repair_capacity(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    axes: list[tuple[str, Callable[[dict[str, Any]], Any]]] = [
        ("predicate", lambda row: row["predicate"]),
        ("subject_object_pair", lambda row: row["subject_object_pair"]),
        ("predicate_x_subject_object_pair", lambda row: (row["predicate"], row["subject_object_pair"])),
        ("subject_object_family_pair", lambda row: row["subject_object_family_pair"]),
        (
            "predicate_x_subject_object_family_pair",
            lambda row: (row["predicate"], row["subject_object_family_pair"]),
        ),
        (
            "predicate_x_subject_object_pair_x_visual_tier",
            lambda row: (row["predicate"], row["subject_object_pair"], row["q_visual_evidence_tier"]),
        ),
    ]
    summaries: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for target in ["p_obs", "p_rel"]:
        for axis, fn in axes:
            summary, top = mixed_capacity(rows, target, axis, fn)
            summaries.append(summary)
            top_rows.extend(top)
    return summaries, top_rows


def key_probe_rows(critical_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in critical_rows:
        if row.get("blocker") in {
            "p_obs:T_subject_object_pair",
            "p_obs:T_predicate_x_class_pair",
            "p_rel_observable:T_subject_object_pair",
            "p_rel_observable:T_predicate_x_class_pair",
        }:
            out.append(
                {
                    "accuracy": float(row.get("accuracy") or 0.0),
                    "blocker": row.get("blocker"),
                    "reason": row.get("reason"),
                    "target_name": row.get("target_name"),
                }
            )
    return out


def route_table(
    repair_capacity: list[dict[str, Any]],
    source_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    by_key = {(row["target"], row["axis"]): row for row in repair_capacity}
    p_rel_exact = by_key[("p_rel", "predicate_x_subject_object_pair")]
    p_obs_exact = by_key[("p_obs", "predicate_x_subject_object_pair")]
    full_train = source_summary.get("full_train_inventory", {})
    rows_by_predicate = full_train.get("rows_by_predicate", {})
    return [
        {
            "decision": "reject",
            "evidence": "allowed T_e class-pair probes solve current p_obs/p_rel targets",
            "reason": "learned smoke would measure class-pair memorization, not attachment observability",
            "route": "run_learned_smoke_now",
        },
        {
            "decision": "reject",
            "evidence": "T_e object labels are the semantic content factor and cannot simply be deleted to hide the shortcut",
            "reason": "feature deletion would weaken the H002 factorization rather than repair the target",
            "route": "drop_subject_object_labels_from_T_e",
        },
        {
            "decision": "reject",
            "evidence": f"current exact predicate x class-pair balanced capacity: p_obs={p_obs_exact['balanced_capacity']}, p_rel={p_rel_exact['balanced_capacity']}",
            "reason": "current 560-row artifact has no exact predicate/class-pair mixed p_obs or p_rel strata",
            "route": "repair_current_560_rows_only",
        },
        {
            "decision": "fallback_not_selected_yet",
            "evidence": "R7 schema is clean and route is conceptually useful, but target is currently shortcut-prone",
            "reason": "freeze only if one targeted repair mining attempt cannot produce balanced contrast rows",
            "route": "freeze_R7_as_diagnostic_now",
        },
        {
            "decision": "selected_next",
            "evidence": (
                f"full train has attached={rows_by_predicate.get('attached to')}, "
                f"hanging={rows_by_predicate.get('hanging on')}; current artifact repair failed because labels were sampled by class-pair strata"
            ),
            "reason": "mine new candidate packets under exact predicate and subject/object class-pair quotas, then label/audit before smoke",
            "route": "full_train_class_pair_balanced_repair_mining",
        },
        {
            "decision": "defer",
            "evidence": "connected to has no explicit topology/functional source evidence",
            "reason": "keep connected-to diagnostic until topology or functional connection evidence is available",
            "route": "promote_connected_to_primary",
        },
        {
            "decision": "reject",
            "evidence": "path decision is hypothesis-stage only and no learned smoke was run",
            "reason": "no paper-level reliability claim can be made from the current R7 artifact",
            "route": "promote_R7_to_paper_evidence",
        },
    ]


def next_mining_contract(source_summary: dict[str, Any]) -> dict[str, Any]:
    full_train = source_summary.get("full_train_inventory", {})
    return {
        "next_todo": NEXT_TODO,
        "route_id": "R7",
        "selected_predicates": ["attached to", "hanging on"],
        "diagnostic_predicates": ["connected to"],
        "candidate_source": "open3dsg_train_full_r7_candidates",
        "full_train_rows_by_predicate": full_train.get("rows_by_predicate", {}),
        "minimum_goals": {
            "balanced_primary_rows_after_labeling": MIN_REPAIR_ROWS,
            "positive_rows_after_labeling": MIN_REPAIR_POSITIVE_ROWS,
            "exact_predicate_class_pair_mixed_strata": MIN_EXACT_STRATA,
        },
        "required_controls": [
            "exact predicate label within each retained contrast cell",
            "same subject_label and object_label within each retained contrast cell whenever possible",
            "fallback to coarse subject/object family only if exact class-pair capacity fails, and mark as weaker",
            "rank band, query source, source score, candidate bucket, packet id, and review label remain hidden",
            "visual/mesh packets are audit evidence first, not raw model input",
            "do not use validation/test rows",
        ],
        "candidate_mining_strategy": [
            "For each primary predicate, find high-capacity subject/object class-pair cells from full train.",
            "Within each cell, sample likely-positive and likely-negative candidates using only hidden selection queues.",
            "Materialize packets for mixed cells, then label from visual/mesh evidence.",
            "After label ingestion, rerun schema shortcut audit before any learned smoke.",
        ],
        "fallback_if_repair_fails": "freeze_R7_as_diagnostic_observability_route_and_move_next_learned_target_elsewhere",
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "accepted": [
            "R7 materialization is schema-clean.",
            "Current R7 labels are not target-identifiable because allowed semantic class-pair fields reconstruct the target.",
            "R7 remains a valuable observability route, but not with the current 560-row target.",
        ],
        "blocked": [
            "Do not run learned smoke on the current R7 artifact.",
            "Do not claim attachment observability p_obs/p_rel success.",
            "Do not delete object labels from T_e as the only repair.",
            "Do not promote connected-to to primary without topology/functional evidence.",
        ],
        "selected_next": [
            "Attempt one full-train class-pair-balanced R7 repair mining pass.",
            "If repair cannot create mixed exact predicate-class label cells, freeze R7 as diagnostic.",
        ],
    }


def build_report(
    summary: dict[str, Any],
    key_probes: list[dict[str, Any]],
    repair_capacity: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> str:
    by_key = {(row["target"], row["axis"]): row for row in repair_capacity}
    lines = [
        "# H002 R7 Attachment Observability Path Decision",
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
        "## Decision",
        "",
        "Do not run learned smoke on the current 560-row R7 artifact. The selected next step is one targeted full-train class-pair-balanced repair mining pass.",
        "",
        "## Why Current R7 Is Blocked",
        "",
        "| Probe | Target | Accuracy |",
        "| --- | --- | ---: |",
    ]
    for row in key_probes:
        lines.append(f"| `{row['blocker']}` | `{row['target_name']}` | {row['accuracy']:.6f} |")
    lines.extend(
        [
            "",
            "## Current Artifact Repair Capacity",
            "",
            "| Target | Control Axis | Mixed Groups | Balanced Capacity |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for key in [
        ("p_obs", "subject_object_pair"),
        ("p_obs", "predicate_x_subject_object_pair"),
        ("p_rel", "subject_object_pair"),
        ("p_rel", "predicate_x_subject_object_pair"),
    ]:
        row = by_key[key]
        lines.append(f"| `{row['target']}` | `{row['axis']}` | {row['mixed_groups']} | {row['balanced_capacity']} |")
    lines.extend(["", "## Route Verdicts", ""])
    for row in routes:
        lines.append(f"- `{row['route']}`: `{row['decision']}` - {row['reason']}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    materialization_summary = read_json(args.materialization_dir / "summary.json")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    errors = validate_inputs(
        audit_summary,
        materialization_summary,
        source_summary,
        args.audit_dir,
        args.materialization_dir,
        args.source_inventory_dir,
    )

    model_rows = read_jsonl(args.materialization_dir / "model_safe_view.jsonl")
    targets = read_jsonl(args.materialization_dir / "target_manifest.jsonl")
    critical_rows = read_csv(args.audit_dir / "critical_probe_failures.csv")
    joined_targets = target_rows(model_rows, targets)
    repair_capacity, top_strata = current_repair_capacity(joined_targets)
    key_probes = key_probe_rows(critical_rows)
    routes = route_table(repair_capacity, source_summary)
    selected_route = next(row for row in routes if row["decision"] == "selected_next")

    status = STATUS_ERROR if errors else STATUS_READY
    next_todo = "fix_attachment_observability_path_decision_inputs" if errors else NEXT_TODO
    selected_path = "fix_inputs" if errors else SELECTED_PATH
    output_paths = {
        "claim_boundary": args.output_dir / "claim_boundary.json",
        "current_repair_capacity": args.output_dir / "current_repair_capacity.csv",
        "current_repair_top_strata": args.output_dir / "current_repair_top_strata.csv",
        "key_probe_table": args.output_dir / "key_probe_table.csv",
        "next_mining_contract": args.output_dir / "next_mining_contract.json",
        "report": args.output_dir / "report.md",
        "route_decision": args.output_dir / "route_decision.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    exact_prel = next(
        row for row in repair_capacity if row["target"] == "p_rel" and row["axis"] == "predicate_x_subject_object_pair"
    )
    exact_pobs = next(
        row for row in repair_capacity if row["target"] == "p_obs" and row["axis"] == "predicate_x_subject_object_pair"
    )
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_path_decision",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_audit_status": audit_summary.get("status"),
        "input_paths": {
            "audit_summary": rel_path(args.audit_dir / "summary.json"),
            "materialization_summary": rel_path(args.materialization_dir / "summary.json"),
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
        },
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "repair_capacity": {
            "current_exact_predicate_class_pair_p_obs_balanced_capacity": exact_pobs["balanced_capacity"],
            "current_exact_predicate_class_pair_p_rel_balanced_capacity": exact_prel["balanced_capacity"],
            "current_repair_feasible": False,
            "minimum_repair_rows": MIN_REPAIR_ROWS,
        },
        "route_verdicts": {row["route"]: row["decision"] for row in routes},
        "schema_version": SCHEMA_VERSION,
        "selected_next_route": selected_route["route"],
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(errors),
    }

    write_csv(output_paths["current_repair_capacity"], repair_capacity)
    write_csv(output_paths["current_repair_top_strata"], top_strata)
    write_csv(output_paths["key_probe_table"], key_probes)
    write_csv(output_paths["route_decision"], routes)
    write_json(output_paths["next_mining_contract"], next_mining_contract(source_summary))
    write_json(output_paths["claim_boundary"], claim_boundary())
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary, key_probes, repair_capacity, routes), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
