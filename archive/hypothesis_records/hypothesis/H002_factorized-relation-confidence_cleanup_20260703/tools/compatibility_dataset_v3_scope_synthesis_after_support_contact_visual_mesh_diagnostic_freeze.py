#!/usr/bin/env python3
"""Synthesize H002 scope after support/contact visual-mesh diagnostic freeze."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_VISUAL_FREEZE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion"
)
DEFAULT_RELATIONSHIPS_TRAIN = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json"
)
DEFAULT_TRAIN_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_PREDICATE_MAPPING = (
    REPO_ROOT / "experiments/H001_geom_reliability/sources/open3dsg/metric_scope/predicate_mapping.json"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"
)

EXPECTED_VISUAL_FREEZE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic"
)
EXPECTED_VISUAL_FREEZE_NEXT = "compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_v1"
STATUS_READY = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_input_errors"
SELECTED_PATH = "all_relation_family_generalization_scan_with_proximity_first"
NEXT_TODO = "compatibility_dataset_v3_relation_family_generalization_capacity_scan"

FALLBACK_FAMILY_MAP = {
    "background_none": ["none"],
    "proximity": ["close by"],
    "relative_vertical": ["higher than", "lower than"],
    "support_contact": ["standing on", "lying on", "supported by"],
    "relative_horizontal": ["left", "right", "front", "behind", "in front of"],
    "attachment_deferred": ["attached to", "hanging on", "mounted on", "connected to"],
    "size_relative": ["bigger than", "smaller than"],
    "identity_symmetry": ["same as", "same symmetry as"],
    "containment_in": ["inside", "standing in", "lying in", "hanging in"],
    "part_structural": ["part of", "belonging to", "build in", "cover", "leaning against"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual-freeze-dir", type=Path, default=DEFAULT_VISUAL_FREEZE_DIR)
    parser.add_argument("--relationships-train", type=Path, default=DEFAULT_RELATIONSHIPS_TRAIN)
    parser.add_argument("--train-rga-dir", type=Path, default=DEFAULT_TRAIN_RGA_DIR)
    parser.add_argument("--predicate-mapping", type=Path, default=DEFAULT_PREDICATE_MAPPING)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_family_map(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return FALLBACK_FAMILY_MAP
    payload = read_json(path)
    raw = payload.get("predicate_family_map") or FALLBACK_FAMILY_MAP
    out: dict[str, list[str]] = {}
    for family, labels in raw.items():
        out[str(family)] = [str(label) for label in labels]
    # Split unsupported bucket into method-useful subfamilies for H002 planning.
    unsupported = set(out.pop("unsupported_first_pass", []))
    for family, labels in FALLBACK_FAMILY_MAP.items():
        if family not in out:
            selected = [label for label in labels if label in unsupported or label in labels]
            out[family] = selected
    return out


def count_gt_predicates(path: Path) -> tuple[int, int, Counter[str]]:
    payload = read_json(path)
    counts: Counter[str] = Counter()
    scans = 0
    relations = 0
    for scan in payload.get("scans", []):
        scans += 1
        for relation in scan.get("relationships", []):
            if len(relation) >= 4:
                counts[str(relation[3])] += 1
                relations += 1
    return scans, relations, counts


def count_queue_predicates(queue_dir: Path) -> tuple[Counter[str], Counter[str], dict[str, Counter[str]]]:
    predicate_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    by_queue: dict[str, Counter[str]] = {}
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = queue_dir / name
        counter: Counter[str] = Counter()
        if not path.exists():
            by_queue[name] = counter
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                predicate = str(row.get("predicate_label"))
                family = str(row.get("predicate_family"))
                predicate_counts[predicate] += 1
                family_counts[family] += 1
                counter[predicate] += 1
        by_queue[name] = counter
    return predicate_counts, family_counts, by_queue


def validate_inputs(visual_freeze: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if visual_freeze.get("status") != EXPECTED_VISUAL_FREEZE_STATUS:
        errors.append({"error_type": "unexpected_visual_freeze_status", "actual": visual_freeze.get("status")})
    if visual_freeze.get("next_todo") != EXPECTED_VISUAL_FREEZE_NEXT:
        errors.append({"error_type": "unexpected_visual_freeze_next_todo", "actual": visual_freeze.get("next_todo")})
    if visual_freeze.get("validation_errors") != 0:
        errors.append({"error_type": "visual_freeze_validation_errors_present", "actual": visual_freeze.get("validation_errors")})
    boundary = visual_freeze.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    for label, path in [
        ("relationships_train", args.relationships_train),
        ("train_hl_queue", args.train_rga_dir / "train_hl_queue.jsonl"),
        ("train_lh_queue", args.train_rga_dir / "train_lh_queue.jsonl"),
    ]:
        if not path.exists():
            errors.append({"error_type": "missing_input", "label": label, "path": rel_path(path)})
    return errors


def predicate_rows(
    official_predicates: list[str],
    gt_counts: Counter[str],
    queue_counts: Counter[str],
    by_queue: dict[str, Counter[str]],
    family_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    pred_to_family: dict[str, str] = {}
    for family, labels in family_map.items():
        for label in labels:
            pred_to_family.setdefault(label, family)
    rows: list[dict[str, Any]] = []
    for predicate in official_predicates:
        gt_count = gt_counts.get(predicate, 0)
        queue_count = queue_counts.get(predicate, 0)
        rows.append(
            {
                "predicate_label": predicate,
                "family": pred_to_family.get(predicate, "unmapped"),
                "open3dsg_train_full_gt_count": gt_count,
                "h002_queue_count": queue_count,
                "h002_hl_count": by_queue.get("train_hl_queue.jsonl", Counter()).get(predicate, 0),
                "h002_lh_count": by_queue.get("train_lh_queue.jsonl", Counter()).get(predicate, 0),
                "in_current_h002_queue": queue_count > 0,
                "observed_in_train_full_gt": gt_count > 0,
            }
        )
    rows.sort(key=lambda row: (-int(row["open3dsg_train_full_gt_count"]), row["predicate_label"]))
    return rows


def family_rows(
    family_map: dict[str, list[str]],
    gt_counts: Counter[str],
    queue_counts: Counter[str],
    visual_freeze: dict[str, Any],
) -> list[dict[str, Any]]:
    freeze_key = visual_freeze.get("key_shortcut_diagnostics", {})
    rows: list[dict[str, Any]] = []
    for family, labels in family_map.items():
        total_gt = sum(gt_counts.get(label, 0) for label in labels)
        total_queue = sum(queue_counts.get(label, 0) for label in labels)
        if family == "proximity":
            priority = 1
            verdict = "selected_first_active_probe"
            rationale = "large GT/queue mass; directly tests whether distance-scale G_e can support C_e beyond source score"
            risk = "dense relation noise; can collapse to distance-only verifier unless hard negatives are controlled"
            next_action = "capacity scan for close by with distance/scale/coverage and same-distance hard negatives"
        elif family == "support_contact":
            priority = 2
            verdict = "individual_predicate_probe_possible_not_grouped_main"
            rationale = "standing on and lying on may behave differently; supported by is sparse and broad"
            risk = (
                "visual-mesh class-pair repair remains shortcut-prone; "
                f"predicate_x_class_pair p_rel majority accuracy "
                f"{freeze_key.get('p_rel_predicate_x_class_pair', {}).get('majority_rule_accuracy')}"
            )
            next_action = "do not rerun grouped target; optional per-predicate capacity scan after close by"
        elif family == "relative_vertical":
            priority = 3
            verdict = "already_clean_anchor"
            rationale = "current clean C_e anchor; keep for method validation"
            risk = "too narrow if used alone"
            next_action = "keep as anchor and compare against new family probes"
        elif family == "size_relative":
            priority = 4
            verdict = "optional_quick_probe"
            rationale = "geometry evidence from OBB volume/extent is direct"
            risk = "may be too similar to scalar geometric rule; novelty weak as main"
            next_action = "scan after proximity if generality table needs another cheap family"
        elif family == "containment_in":
            priority = 5
            verdict = "optional_schema_probe"
            rationale = "could use containment ratio, but labels are sparse/heterogeneous"
            risk = "inside missing in train_full GT and in-predicates are sparse"
            next_action = "schema/capacity scan only, not immediate main"
        elif family == "attachment_deferred":
            priority = 6
            verdict = "defer_visual_mesh_heavy"
            rationale = "high novelty but needs visual/mesh/observability labels"
            risk = "expensive audit and sparse positives for hanging/connected"
            next_action = "defer until proximity/general scan is summarized"
        elif family == "relative_horizontal":
            priority = 7
            verdict = "defer_reference_frame_ambiguity"
            rationale = "large GT count but frame convention is ambiguous"
            risk = "may test coordinate-frame convention rather than relation reliability"
            next_action = "needs explicit reference-frame protocol"
        else:
            priority = 8
            verdict = "defer_or_diagnostic"
            rationale = "relation semantics are not immediately geometry-checkable under current G_e"
            risk = "semantic ontology or annotation convention may dominate"
            next_action = "include in all-relation inventory, not first active probe"
        rows.append(
            {
                "family": family,
                "predicates": "; ".join(labels),
                "open3dsg_train_full_gt_total": total_gt,
                "h002_queue_total": total_queue,
                "priority": priority,
                "verdict": verdict,
                "rationale": rationale,
                "main_risk": risk,
                "next_action": next_action,
            }
        )
    rows.sort(key=lambda row: (int(row["priority"]), -int(row["open3dsg_train_full_gt_total"]), row["family"]))
    return rows


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "run_all_relation_type_model_now",
            "verdict": "reject",
            "reason": "Running models before target eligibility would repeat the support/contact shortcut issue.",
            "paper_risk": "appears as cherry-picking if only successful families become main results",
        },
        {
            "route": "all_relation_family_capacity_scan",
            "verdict": "selected",
            "reason": "Define the same target-identifiability gates for every relation type before choosing paper-facing families.",
            "paper_risk": "manageable if pass/fail criteria are reported for all families",
        },
        {
            "route": "proximity_close_by_first",
            "verdict": "selected_first_active_family",
            "reason": "close by has the largest GT count and current H002 queue mass, so it is the most practical next probe.",
            "paper_risk": "must avoid a trivial distance-only verifier claim",
        },
        {
            "route": "support_contact_individual_predicate_scan",
            "verdict": "defer_after_proximity_or_parallel_diagnostic",
            "reason": "standing on, lying on, and supported by can behave differently; grouped support/contact failure does not prove each predicate fails.",
            "paper_risk": "current visual-mesh proxy target still has predicate/class shortcuts",
        },
        {
            "route": "main_claim_only_on_successful_families",
            "verdict": "reject_as_framing",
            "reason": "The paper can emphasize successful families, but the protocol must disclose attempted families and failure causes.",
            "paper_risk": "strong cherry-picking objection if failure families are hidden",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], families: list[dict[str, Any]], predicates: list[dict[str, Any]]) -> None:
    top_predicates = [row for row in predicates if int(row["open3dsg_train_full_gt_count"]) > 0]
    lines = [
        "# H002 Scope Synthesis After Support/Contact Visual-Mesh Diagnostic Freeze",
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
        "Proceed with an all-relation-family eligibility scan, with `close by` / proximity as the first active probe.",
        "",
        "This is not a plan to hide failed relation types. The paper-facing protocol should report which relation families pass or fail the target-identifiability gates, then use successful families as main evidence and failed families as a failure taxonomy.",
        "",
        "## Why Not Model All Relations Immediately?",
        "",
        "The support/contact visual-mesh repair showed that row count is not enough. A target can have usable positive/negative mass and still be solved by `predicate + class-pair` without using geometry. Therefore every relation type first needs the same eligibility audit.",
        "",
        "## Family Priorities",
        "",
    ]
    for row in families:
        lines.extend(
            [
                f"- `{row['family']}`: {row['verdict']}",
                f"  Predicates: {row['predicates']}",
                f"  Train GT total: {row['open3dsg_train_full_gt_total']}; H002 queue total: {row['h002_queue_total']}",
                f"  Rationale: {row['rationale']}",
                f"  Risk: {row['main_risk']}",
                f"  Next: {row['next_action']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Open3DSG Train-Full Predicate Counts",
            "",
            "```text",
        ]
    )
    for row in top_predicates:
        lines.append(f"{row['predicate_label']}\t{row['open3dsg_train_full_gt_count']}")
    lines.extend(
        [
            "```",
            "",
            "Official predicates with zero train-full GT count are retained in the inventory when they appear in the mapping, but they are not immediate H002 targets.",
            "",
            "## Boundary",
            "",
            "- Train-only scope synthesis.",
            "- No validation/test usage.",
            "- No row materialization.",
            "- No learned smoke or model training.",
            "- No paper evidence.",
            "- No H001 artifact modification.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    validation_errors: list[dict[str, Any]] = []
    visual_summary_path = args.visual_freeze_dir / "summary.json"
    if visual_summary_path.exists():
        visual_freeze = read_json(visual_summary_path)
    else:
        visual_freeze = {}
        validation_errors.append({"error_type": "missing_visual_freeze_summary", "path": rel_path(visual_summary_path)})
    validation_errors.extend(validate_inputs(visual_freeze, args))

    family_map = load_family_map(args.predicate_mapping)
    official_predicates = sorted({label for labels in family_map.values() for label in labels})
    scans = 0
    relations = 0
    gt_counts: Counter[str] = Counter()
    queue_counts: Counter[str] = Counter()
    queue_family_counts: Counter[str] = Counter()
    by_queue: dict[str, Counter[str]] = {}
    if args.relationships_train.exists():
        scans, relations, gt_counts = count_gt_predicates(args.relationships_train)
        official_predicates = sorted(set(official_predicates) | set(gt_counts))
    if args.train_rga_dir.exists():
        queue_counts, queue_family_counts, by_queue = count_queue_predicates(args.train_rga_dir)
        official_predicates = sorted(set(official_predicates) | set(queue_counts))

    predicate_table = predicate_rows(official_predicates, gt_counts, queue_counts, by_queue, family_map)
    family_table = family_rows(family_map, gt_counts, queue_counts, visual_freeze)
    routes = route_rows()

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_VISUAL_FREEZE_NEXT
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO

    output_paths = {
        "all_relation_types": args.output_dir / "all_relation_types.csv",
        "family_priority_table": args.output_dir / "family_priority_table.csv",
        "report": args.output_dir / "report.md",
        "route_decision": args.output_dir / "route_decision.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_scope_synthesis",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "predicate_mapping": rel_path(args.predicate_mapping),
            "relationships_train": rel_path(args.relationships_train),
            "train_rga_dir": rel_path(args.train_rga_dir),
            "visual_freeze_summary": rel_path(visual_summary_path),
        },
        "next_todo": next_todo,
        "open3dsg_train_full": {
            "scans": scans,
            "relations": relations,
            "unique_predicates_with_gt": sum(1 for count in gt_counts.values() if count > 0),
            "official_or_mapped_predicates": len(official_predicates),
        },
        "output_paths": {name: rel_path(path) for name, path in output_paths.items()},
        "queue_summary": {
            "predicate_counts": dict(queue_counts),
            "family_counts": dict(queue_family_counts),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "selected_first_active_family": "proximity",
        "selected_first_active_predicates": ["close by"],
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["all_relation_types"], predicate_table)
    write_csv(output_paths["family_priority_table"], family_table)
    write_csv(output_paths["route_decision"], routes)
    write_report(output_paths["report"], summary, family_table, predicate_table)

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
                "selected_first_active_family": "proximity",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
