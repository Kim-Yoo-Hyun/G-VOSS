#!/usr/bin/env python3
"""Plan the next repair after the H002 attachment independent target audit."""

from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_audit_label_ingestion_v1"
AUDIT_DIR = H2_ROOT / "artifacts/attachment_independent_target_independence_audit_v1"
SUBSET_PLAN_DIR = H2_ROOT / "artifacts/attachment_independent_audit_subset_plan_v1"
CANDIDATE_DIR = H2_ROOT / "artifacts/attachment_controlled_candidates_v1"
V23_BLOCKER_DIR = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/"
    / "reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis"
)
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_target_repair_plan_v1"

EXPECTED_AUDIT_STATUS = "h002_attachment_independent_target_independence_audit_blocked_primary_positive_sparse"
EXPECTED_AUDIT_NEXT = "attachment_independent_target_repair_plan_v1"

SCHEMA_VERSION = "h002_attachment_independent_target_repair_plan_v1"
STATUS_READY = "h002_attachment_independent_target_repair_plan_v1_ready"
STATUS_ERROR = "h002_attachment_independent_target_repair_plan_v1_errors"
NEXT_TODO = "attachment_independent_positive_anchor_mining_plan_v1"

POSTERIOR_MIN_POSITIVE = 30
RECOMMENDED_MIN_POSITIVE = 60
RECOMMENDED_MIN_NEGATIVE = 60
RECOMMENDED_MIN_MIXED_VISIBLE_PAIR_GROUPS = 10


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
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


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


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_fill_module():
    script = H2_ROOT / "tools/attachment_independent_audit_label_fill_v1.py"
    spec = importlib.util.spec_from_file_location("attachment_independent_audit_label_fill_v1", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_planner_module():
    script = H2_ROOT / "tools/attachment_independent_audit_subset_plan_v1.py"
    spec = importlib.util.spec_from_file_location("attachment_independent_audit_subset_plan_v1", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate_visible_label(row: dict[str, Any], fill_module: Any, evidence_tier: str | None = None) -> dict[str, Any]:
    te = row["T_e"]
    hidden = row["hidden_control"]
    tier = evidence_tier
    if tier is None:
        tier = (
            "T1_strong_pair_visual"
            if hidden.get("capacity_evidence_tier_hidden") == "E_pos_supported_witness"
            else "T2_individual_visual_plus_mesh"
        )
    fake = {
        "subject_label": te["subject_label"],
        "predicate_label": te["predicate_label"],
        "object_label": te["object_label"],
        "evidence_tier": tier,
        "packet_role": (
            "connected_diagnostic_only"
            if row.get("row_role") == "connected_diagnostic"
            else "primary_attachment_reliability_candidate"
        ),
    }
    if fake["packet_role"] == "connected_diagnostic_only":
        rel, geom, endpoint, coverage, uncertainty, notes = fill_module.fill_connected(fake)
    else:
        rel, geom, endpoint, coverage, uncertainty, notes = fill_module.fill_primary(fake)
    return {
        "review_relation_reliability": rel,
        "review_geometry_support": geom,
        "review_endpoint_identity": endpoint,
        "review_coverage": coverage,
        "review_uncertainty": uncertainty,
        "review_notes": notes,
        "subject_label": te["subject_label"],
        "predicate_label": te["predicate_label"],
        "object_label": te["object_label"],
        "subject_object_visible_pair": f"{te['subject_label']}|{te['object_label']}",
        "evidence_tier": tier,
        "row_role": row.get("row_role"),
        "cell_id_hidden": hidden.get("cell_id_hidden"),
        "proxy_role_hidden": hidden.get("proxy_role_hidden"),
        "rank_band_hidden": hidden.get("rank_band_hidden"),
    }


def binary_capacity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [row for row in rows if row.get("row_role") == "primary_binary" and row["review_relation_reliability"] != "abstain_uncertain"]
    counts = Counter(row["review_relation_reliability"] for row in usable)
    pred_counts = Counter((row["predicate_label"], row["review_relation_reliability"]) for row in usable)
    pair_groups: dict[str, Counter[str]] = defaultdict(Counter)
    pred_pair_groups: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    cell_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in usable:
        y = "positive" if row["review_relation_reliability"] == "accept_reliable" else "negative"
        pair_groups[row["subject_object_visible_pair"]][y] += 1
        pred_pair_groups[(row["predicate_label"], row["subject_object_visible_pair"])][y] += 1
        cell_groups[row["cell_id_hidden"]][y] += 1
    mixed_pairs = {key: dict(value) for key, value in pair_groups.items() if len(value) > 1}
    mixed_pred_pairs = {f"{key[0]}|{key[1]}": dict(value) for key, value in pred_pair_groups.items() if len(value) > 1}
    return {
        "usable_binary_rows": len(usable),
        "accept_positive": counts.get("accept_reliable", 0),
        "reject_negative": counts.get("reject_unreliable", 0),
        "predicate_reliability_counts": {f"{pred}|{label}": count for (pred, label), count in sorted(pred_counts.items())},
        "visible_pair_groups": len(pair_groups),
        "mixed_visible_pair_groups": len(mixed_pairs),
        "mixed_visible_pair_balanced_rows": sum(2 * min(value.values()) for value in mixed_pairs.values()),
        "mixed_predicate_visible_pair_groups": len(mixed_pred_pairs),
        "mixed_predicate_visible_pair_balanced_rows": sum(2 * min(value.values()) for value in mixed_pred_pairs.values()),
        "cell_binary_counts": {key: dict(value) for key, value in sorted(cell_groups.items())},
        "example_mixed_visible_pairs": dict(list(sorted(mixed_pairs.items()))[:20]),
    }


def matched_candidate_labels(candidates: list[dict[str, Any]], fill_module: Any) -> list[dict[str, Any]]:
    planner = load_planner_module()
    visible = planner.load_v20_visible()
    output: list[dict[str, Any]] = []
    for row in candidates:
        match = planner.match_v20(row, visible)
        if not match:
            continue
        label = candidate_visible_label(row, fill_module, evidence_tier=match.get("evidence_tier") or None)
        label["packet_id"] = match.get("packet_id")
        label["v20_packet_matched"] = True
        output.append(label)
    return output


def validate_inputs(audit_summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    for row in rows:
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "packet_id": row.get("packet_id")})
    return errors


def route_table(current_capacity: dict[str, Any], matched_capacity: dict[str, Any], full_capacity: dict[str, Any], v23: dict[str, Any] | None) -> list[dict[str, Any]]:
    v23_root = ""
    if v23:
        v23_root = v23.get("blocker_synthesis", {}).get("root_cause", "")
    return [
        {
            "route": "use_current_200_as_is",
            "verdict": "reject",
            "reason": "Primary p_rel/C_e has only 17 positives and no clear controlled slice.",
            "positive_rows": current_capacity["accept_positive"],
            "negative_rows": current_capacity["reject_negative"],
            "mixed_visible_pair_groups": current_capacity["mixed_visible_pair_groups"],
            "next_action": "do_not_train_posterior",
        },
        {
            "route": "use_all_v20_matched_298",
            "verdict": "reject",
            "reason": "Using every already materialized v20 packet still gives only 24 positives, below the posterior smoke threshold.",
            "positive_rows": matched_capacity["accept_positive"],
            "negative_rows": matched_capacity["reject_negative"],
            "mixed_visible_pair_groups": matched_capacity["mixed_visible_pair_groups"],
            "next_action": "do_not_train_posterior",
        },
        {
            "route": "materialize_unmatched_102_and_use_all_400",
            "verdict": "diagnostic_only",
            "reason": "Full candidate pool would reach 45 positives, but attached-to remains sparse and predicate-visible-pair contrast is still absent.",
            "positive_rows": full_capacity["accept_positive"],
            "negative_rows": full_capacity["reject_negative"],
            "mixed_visible_pair_groups": full_capacity["mixed_visible_pair_groups"],
            "next_action": "only_if_needed_for_diagnostic_packet_coverage",
        },
        {
            "route": "relax_uncertain_or_label_policy_to_create_positives",
            "verdict": "reject",
            "reason": "This would tune the target to satisfy the model rather than repair independent evidence.",
            "positive_rows": None,
            "negative_rows": None,
            "mixed_visible_pair_groups": None,
            "next_action": "keep_label_policy_strict",
        },
        {
            "route": "new_positive_anchor_mining_with_packet_materialization",
            "verdict": "selected",
            "reason": "The current bottleneck is independent accept-positive evidence. Repair must mine more high-precision positive anchors and matched hard negatives before posterior smoke.",
            "positive_rows": f"target >= {RECOMMENDED_MIN_POSITIVE}",
            "negative_rows": f"target >= {RECOMMENDED_MIN_NEGATIVE}",
            "mixed_visible_pair_groups": f"target >= {RECOMMENDED_MIN_MIXED_VISIBLE_PAIR_GROUPS}",
            "next_action": NEXT_TODO,
        },
        {
            "route": "freeze_attachment_as_diagnostic_only",
            "verdict": "fallback",
            "reason": f"Prior v23 blocker also indicates controlled-cell diversity is hard: {v23_root or 'v23 blocker unavailable'}.",
            "positive_rows": None,
            "negative_rows": None,
            "mixed_visible_pair_groups": None,
            "next_action": "use_attachment_only_as_relation-family failure taxonomy if mining fails",
        },
    ]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    current = summary["capacity"]["current_200"]
    matched = summary["capacity"]["all_v20_matched_298"]
    full = summary["capacity"]["full_candidate_400_visible_rule"]
    lines = [
        "# H002 Attachment Independent Target Repair Plan V1",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_route = {summary['selected_route']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Capacity Check",
        "",
        "```text",
        f"current_200 positive/negative = {current['accept_positive']} / {current['reject_negative']}",
        f"all_v20_matched_298 positive/negative = {matched['accept_positive']} / {matched['reject_negative']}",
        f"full_candidate_400 visible-rule positive/negative = {full['accept_positive']} / {full['reject_negative']}",
        f"full_candidate_400 mixed_visible_pair_groups = {full['mixed_visible_pair_groups']}",
        f"full_candidate_400 mixed_predicate_visible_pair_groups = {full['mixed_predicate_visible_pair_groups']}",
        "```",
        "",
        "## Decision",
        "",
        "Do not train a posterior from the current attachment target. Do not relax labels. The selected repair is to mine new high-precision positive-anchor candidates and matched hard negatives with packet materialization, then rerun independent label fill/ingestion/target-independence audit.",
        "",
        "## Why",
        "",
        "- Current 200-row audit has only 17 accept positives.",
        "- Already materialized v20 packet rows would only raise this to 24 positives.",
        "- Full 400-row candidate pool could reach 45 positives, but same predicate-visible-pair contrast is still absent.",
        "- The target failure is therefore not a posterior-combiner issue; it is independent positive evidence and controlled-contrast construction.",
        "",
        "## Repair Requirements",
        "",
        f"- mine at least `{RECOMMENDED_MIN_POSITIVE}` accept-positive and `{RECOMMENDED_MIN_NEGATIVE}` reject-negative primary rows before posterior smoke;",
        f"- obtain at least `{RECOMMENDED_MIN_MIXED_VISIBLE_PAIR_GROUPS}` mixed visible-pair or endpoint-family groups;",
        "- keep `attached to` and `hanging on` separately reported; if `attached to` cannot reach class mass, keep it diagnostic;",
        "- labels must come from visible/mesh audit evidence after source/proxy fields are hidden;",
        "- source rank, proxy role, cell id, and prior labels remain diagnostic-only.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fill_module = load_fill_module()

    ingestion_rows = read_jsonl(INGESTION_DIR / "ingested_rows.jsonl")
    audit_summary = read_json(AUDIT_DIR / "summary.json")
    candidates = read_jsonl(CANDIDATE_DIR / "candidate_rows.jsonl")
    errors = validate_inputs(audit_summary, ingestion_rows)

    current_rows = [
        {
            "row_role": "primary_binary" if row.get("is_primary_relation_target") else "connected_diagnostic",
            "review_relation_reliability": row["review_relation_reliability"],
            "predicate_label": row["predicate_label"],
            "subject_object_visible_pair": row["subject_object_visible_pair"],
            "cell_id_hidden": row["cell_id_hidden"],
        }
        for row in ingestion_rows
    ]

    full_labeled = [candidate_visible_label(row, fill_module) for row in candidates]
    matched_labeled = matched_candidate_labels(candidates, fill_module)

    current_capacity = binary_capacity(current_rows)
    matched_capacity = binary_capacity(matched_labeled)
    full_capacity = binary_capacity(full_labeled)

    v23_summary = read_json(V23_BLOCKER_DIR / "summary.json") if (V23_BLOCKER_DIR / "summary.json").exists() else None
    routes = route_table(current_capacity, matched_capacity, full_capacity, v23_summary)

    status = STATUS_ERROR if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_route": "new_positive_anchor_mining_with_packet_materialization",
        "decision": "repair_target_before_any_posterior_smoke",
        "next_todo": NEXT_TODO if not errors else EXPECTED_AUDIT_NEXT,
        "validation_errors": len(errors),
        "input_paths": {
            "ingested_rows": rel_path(INGESTION_DIR / "ingested_rows.jsonl"),
            "target_independence_summary": rel_path(AUDIT_DIR / "summary.json"),
            "candidate_rows_400": rel_path(CANDIDATE_DIR / "candidate_rows.jsonl"),
            "subset_plan_summary": rel_path(SUBSET_PLAN_DIR / "summary.json"),
            "v23_blocker_summary": rel_path(V23_BLOCKER_DIR / "summary.json") if v23_summary else None,
        },
        "capacity": {
            "current_200": current_capacity,
            "all_v20_matched_298": matched_capacity,
            "full_candidate_400_visible_rule": full_capacity,
        },
        "requirements": {
            "posterior_min_positive": POSTERIOR_MIN_POSITIVE,
            "recommended_min_positive": RECOMMENDED_MIN_POSITIVE,
            "recommended_min_negative": RECOMMENDED_MIN_NEGATIVE,
            "recommended_min_mixed_visible_pair_groups": RECOMMENDED_MIN_MIXED_VISIBLE_PAIR_GROUPS,
            "label_policy": "do_not_relax_uncertain_to_accept",
            "posterior_smoke_allowed": False,
        },
        "routes": routes,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "output_paths": {
            "summary": rel_path(OUT_DIR / "summary.json"),
            "report": rel_path(OUT_DIR / "report.md"),
            "route_table": rel_path(OUT_DIR / "route_table.csv"),
            "full_candidate_visible_rule_labels": rel_path(OUT_DIR / "full_candidate_visible_rule_labels.jsonl"),
            "matched_candidate_visible_rule_labels": rel_path(OUT_DIR / "matched_candidate_visible_rule_labels.jsonl"),
            "validation_errors": rel_path(OUT_DIR / "validation_errors.jsonl"),
        },
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_csv(OUT_DIR / "route_table.csv", routes)
    write_jsonl(OUT_DIR / "full_candidate_visible_rule_labels.jsonl", full_labeled)
    write_jsonl(OUT_DIR / "matched_candidate_visible_rule_labels.jsonl", matched_labeled)
    write_jsonl(OUT_DIR / "validation_errors.jsonl", errors)
    write_report(OUT_DIR / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"next={summary['next_todo']}")
    print(f"current_positive={current_capacity['accept_positive']}")
    print(f"matched_positive={matched_capacity['accept_positive']}")
    print(f"full_candidate_positive={full_capacity['accept_positive']}")
    print(f"full_mixed_predicate_visible_pair_groups={full_capacity['mixed_predicate_visible_pair_groups']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
