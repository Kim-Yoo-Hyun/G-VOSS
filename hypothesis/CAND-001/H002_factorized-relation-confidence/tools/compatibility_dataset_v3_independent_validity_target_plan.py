#!/usr/bin/env python3
"""Plan an independent train-side validity target for H002 after the two-family C_e proof."""

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

DEFAULT_SYNTHESIS_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_target_plan"
DEFAULT_3DSSG_TRAIN = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_train.json"
DEFAULT_OPEN3DSG_TRAIN_REL = REPO_ROOT / "local_dataset/Open3DSG_staged/training_repro/data/3RScan/relationships.json"
DEFAULT_OPEN3DSG_RAW_DUMP = REPO_ROOT / "experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl"
DEFAULT_MANUAL_LABELS = H2_ROOT / "artifacts/manual_labels/round1_labels.jsonl"
DEFAULT_ATTACHMENT_AUDIT = H2_ROOT / "artifacts/attachment_independent_positive_anchor_target_independence_audit_v1/summary.json"

EXPECTED_SYNTHESIS_STATUS = "h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_target_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_target_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_target_plan_input_errors"
SELECTED_PATH = "select_gt_anchored_train_validity_inventory_before_materialization"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_source_inventory"

PRIMARY_PREDICATES = {
    "relative_vertical": ["higher than", "lower than"],
    "support_contact_pose_conditioned": ["standing on", "lying on"],
}

DIAGNOSTIC_PREDICATES = {
    "support_contact_superordinate": ["supported by"],
    "attachment_like": ["attached to", "hanging on", "connected to"],
    "proximity": ["close by"],
    "relative_horizontal": ["left", "right", "front", "behind"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesis-dir", type=Path, default=DEFAULT_SYNTHESIS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dsg-train", type=Path, default=DEFAULT_3DSSG_TRAIN)
    parser.add_argument("--open3dsg-train-relationships", type=Path, default=DEFAULT_OPEN3DSG_TRAIN_REL)
    parser.add_argument("--open3dsg-raw-dump", type=Path, default=DEFAULT_OPEN3DSG_RAW_DUMP)
    parser.add_argument("--manual-labels", type=Path, default=DEFAULT_MANUAL_LABELS)
    parser.add_argument("--attachment-audit", type=Path, default=DEFAULT_ATTACHMENT_AUDIT)
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


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def count_relationships(path: Path) -> dict[str, Any]:
    result = {
        "exists": path.exists(),
        "path": rel_path(path),
        "scan_records": 0,
        "relationships": 0,
        "predicate_counts": {},
        "selected_counts": {},
    }
    if not path.exists():
        return result
    data = read_json(path)
    scans = data.get("scans", [])
    pred_counts: Counter[str] = Counter()
    for scan in scans:
        result["scan_records"] += 1
        for rel in scan.get("relationships", []):
            if isinstance(rel, list) and len(rel) >= 4:
                predicate = rel[3]
            elif isinstance(rel, dict):
                predicate = rel.get("predicate") or rel.get("relationship")
            else:
                predicate = None
            if predicate is None:
                continue
            pred_counts[str(predicate)] += 1
            result["relationships"] += 1
    result["predicate_counts"] = dict(pred_counts)
    selected: dict[str, int] = {}
    for family, preds in {**PRIMARY_PREDICATES, **DIAGNOSTIC_PREDICATES}.items():
        selected[family] = sum(pred_counts[p] for p in preds)
    result["selected_counts"] = selected
    return result


def manual_label_inventory(path: Path) -> dict[str, Any]:
    inventory = {
        "exists": path.exists(),
        "path": rel_path(path),
        "rows": 0,
        "source_ids": {},
        "final_labels": {},
        "train_side_usable": False,
        "reason": "missing",
    }
    if not path.exists():
        return inventory
    source_ids: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows += 1
            source_ids[str(row.get("source_id"))] += 1
            labels[str(row.get("final_label"))] += 1
    inventory.update(
        {
            "rows": rows,
            "source_ids": dict(source_ids),
            "final_labels": dict(labels),
            "train_side_usable": False,
            "reason": "existing manual labels are validation/no-GT audit artifacts, not train-side H002 independent validity targets",
        }
    )
    return inventory


def attachment_audit_inventory(path: Path) -> dict[str, Any]:
    inventory = {
        "exists": path.exists(),
        "path": rel_path(path),
        "train_side_usable": False,
        "reason": "missing",
    }
    if not path.exists():
        return inventory
    summary = read_json(path)
    inventory.update(
        {
            "status": summary.get("status"),
            "validation_errors": summary.get("validation_errors"),
            "train_side_usable": False,
            "reason": "attachment positive-anchor target has class mass but failed target-independence/controlled-slice promotion",
        }
    )
    return inventory


def validate_inputs(synthesis: dict[str, Any], inventories: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if synthesis.get("status") != EXPECTED_SYNTHESIS_STATUS:
        errors.append({"error_type": "unexpected_synthesis_status", "actual": synthesis.get("status")})
    if synthesis.get("validation_errors") != 0:
        errors.append({"error_type": "synthesis_validation_errors", "actual": synthesis.get("validation_errors")})
    boundary = synthesis.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "synthesis_boundary_not_false", "key": key, "actual": boundary.get(key)})

    dsg = inventories["dsg_train"]
    if not dsg["exists"] or dsg["relationships"] <= 0:
        errors.append({"error_type": "missing_or_empty_dsg_train", "path": dsg["path"]})
    for family in PRIMARY_PREDICATES:
        if dsg["selected_counts"].get(family, 0) <= 0:
            errors.append({"error_type": "missing_primary_family_gt", "family": family})
    raw_rows = inventories["open3dsg_raw_dump"]["rows"]
    if raw_rows <= 0:
        errors.append({"error_type": "missing_open3dsg_raw_dump_rows", "path": inventories["open3dsg_raw_dump"]["path"]})
    return errors


def source_inventory_rows(inventories: dict[str, Any]) -> list[dict[str, Any]]:
    dsg = inventories["dsg_train"]
    open_rel = inventories["open3dsg_train_relationships"]
    rows = [
        {
            "source": "3DSSG_subset_train_GT",
            "path": dsg["path"],
            "exists": dsg["exists"],
            "rows_or_relationships": dsg["relationships"],
            "role": "primary independent label source",
            "decision": "selected_for_inventory",
            "caveat": "GT incompleteness means no-GT rows cannot be automatic negatives",
        },
        {
            "source": "Open3DSG_training_repro_relationships",
            "path": open_rel["path"],
            "exists": open_rel["exists"],
            "rows_or_relationships": open_rel["relationships"],
            "role": "secondary GT/source alignment check",
            "decision": "selected_for_inventory",
            "caveat": "must verify split/subgraph alignment with raw dump before materialization",
        },
        {
            "source": "Open3DSG_train_raw_dump",
            "path": inventories["open3dsg_raw_dump"]["path"],
            "exists": inventories["open3dsg_raw_dump"]["exists"],
            "rows_or_relationships": inventories["open3dsg_raw_dump"]["rows"],
            "role": "candidate source scores Z_e and rank-like evidence",
            "decision": "selected_for_inventory",
            "caveat": "read-only H001 artifact; do not modify or treat validation rows as train",
        },
        {
            "source": "manual_round1_labels",
            "path": inventories["manual_labels"]["path"],
            "exists": inventories["manual_labels"]["exists"],
            "rows_or_relationships": inventories["manual_labels"]["rows"],
            "role": "diagnostic only",
            "decision": "reject_for_train_target",
            "caveat": inventories["manual_labels"]["reason"],
        },
        {
            "source": "attachment_positive_anchor_audit",
            "path": inventories["attachment_audit"]["path"],
            "exists": inventories["attachment_audit"]["exists"],
            "rows_or_relationships": "see summary",
            "role": "diagnostic only",
            "decision": "reject_for_primary_independent_target",
            "caveat": inventories["attachment_audit"]["reason"],
        },
    ]
    return rows


def family_capacity_rows(inventories: dict[str, Any]) -> list[dict[str, Any]]:
    dsg = inventories["dsg_train"]
    counts = dsg["predicate_counts"]
    rows: list[dict[str, Any]] = []
    for family, preds in PRIMARY_PREDICATES.items():
        rows.append(
            {
                "family": family,
                "predicates": "; ".join(preds),
                "gt_count": sum(counts.get(p, 0) for p in preds),
                "predicate_counts": "; ".join(f"{p}:{counts.get(p, 0)}" for p in preds),
                "target_role": "primary",
                "decision": "include_in_source_inventory",
            }
        )
    for family, preds in DIAGNOSTIC_PREDICATES.items():
        rows.append(
            {
                "family": family,
                "predicates": "; ".join(preds),
                "gt_count": sum(counts.get(p, 0) for p in preds),
                "predicate_counts": "; ".join(f"{p}:{counts.get(p, 0)}" for p in preds),
                "target_role": "diagnostic_or_future",
                "decision": "count_but_do_not_primary_materialize_yet",
            }
        )
    return rows


def target_option_rows() -> list[dict[str, Any]]:
    return [
        {
            "option": "GT_anchored_train_validity",
            "verdict": "selected",
            "label_source_independence": "official train GT predicates are independent from same-G_e constructed labels",
            "positive_policy": "official GT relation rows for relative_vertical and support/contact predicates",
            "negative_policy": "matched predicate-flip or wrong-pair hard negatives only when GT absence plus geometry contradiction and controls agree",
            "abstain_policy": "no-GT but geometry-supported rows become abstain/audit, not negative",
            "main_risk": "GT annotation incompleteness and source/raw-dump alignment",
            "next_action": NEXT_TODO,
        },
        {
            "option": "human_audit_accept_reject",
            "verdict": "defer",
            "label_source_independence": "strong if newly collected from train-side visible evidence",
            "positive_policy": "human accept",
            "negative_policy": "human reject",
            "abstain_policy": "human uncertain",
            "main_risk": "existing labels are validation/no-GT or attachment diagnostic; new packet cost is high",
            "next_action": "use after GT inventory shows hard cases needing audit",
        },
        {
            "option": "cross_source_agreement",
            "verdict": "defer",
            "label_source_independence": "medium, if two independent train-side sources agree",
            "positive_policy": "same pair/predicate agreement plus geometry support",
            "negative_policy": "source conflict plus geometry contradiction",
            "abstain_policy": "one-source-only or annotation-sparse rows",
            "main_risk": "current available cross-source artifacts are mostly validation-side, not train-side",
            "next_action": "inventory after GT route if train-side second source exists",
        },
        {
            "option": "high_precision_geometry_rule_subset",
            "verdict": "auxiliary_only",
            "label_source_independence": "weak because geometry rules overlap with C_e evidence",
            "positive_policy": "only as high-precision anchor or teacher",
            "negative_policy": "never as main negative alone",
            "abstain_policy": "uncertain geometry remains abstain",
            "main_risk": "circularity with geometry evidence",
            "next_action": "use as stratification/control, not target owner",
        },
        {
            "option": "no_GT_as_negative",
            "verdict": "reject",
            "label_source_independence": "invalid under incomplete 3DSSG annotation",
            "positive_policy": "n/a",
            "negative_policy": "forbidden",
            "abstain_policy": "no-GT rows require audit or special handling",
            "main_risk": "turns annotation sparsity into false negatives",
            "next_action": "do_not_use",
        },
    ]


def selected_target_contract() -> dict[str, Any]:
    return {
        "target_name": "GT_anchored_train_validity_target",
        "purpose": "Test whether C_e helps relation validity beyond constructed same-G_e compatibility labels.",
        "split_policy": "train_only",
        "primary_families": PRIMARY_PREDICATES,
        "diagnostic_families": DIAGNOSTIC_PREDICATES,
        "label_axes": {
            "C_e_validity": {
                "positive": "GT predicate and geometry evidence are compatible",
                "negative": "matched counterfactual predicate or wrong-pair candidate is geometry-incompatible and not GT-supported",
                "abstain": "no-GT but geometry-supported, low coverage, or annotation-sparse case",
            },
            "p_obs": {
                "observable": "OBB/geometry evidence available and no critical feature missing",
                "abstain_or_unobservable": "coverage insufficient, visual/mesh needed, or geometry ambiguous",
            },
            "p_rel": {
                "accept": "observable GT-supported relation candidate",
                "reject": "observable matched hard negative with geometry contradiction",
                "abstain": "annotation-sparse, no-GT geometry-supported, or low observability",
            },
        },
        "forbidden_shortcuts": [
            "row_id",
            "gt_label_self",
            "construction_label",
            "hidden_counterfactual_type",
            "scan_id",
            "directed_pair_id",
            "raw_predicate_id",
            "target_y",
        ],
        "required_pre_smoke_controls": [
            "source-only Z_e",
            "semantic-only T_e",
            "geometry-only G_e",
            "plain T_e+G_e concat",
            "interaction C_e",
            "wrong-T same-G control",
            "shuffled-G within-family control",
            "same-rank-band control",
            "same-object-family control",
            "same-scan grouped split",
        ],
        "minimum_inventory_questions": [
            "How many GT-positive anchors exist per family?",
            "How many anchors have source Z_e/rank from Open3DSG train raw dump?",
            "How many anchors have usable geometry evidence G_e?",
            "How many hard negatives can be matched without using no-GT as a naive negative?",
            "Can class mass and shortcut controls pass before learned smoke?",
        ],
    }


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Inventory GT anchors, source score availability, geometry evidence availability, and matched-hard-negative capacity before materializing any independent validity rows.",
        "inputs": [
            rel_path(DEFAULT_3DSSG_TRAIN),
            rel_path(DEFAULT_OPEN3DSG_TRAIN_REL),
            rel_path(DEFAULT_OPEN3DSG_RAW_DUMP),
        ],
        "outputs_required": [
            "GT-positive count by family/predicate",
            "source Z_e join count by scan/pair/predicate",
            "geometry G_e join count by family",
            "hard-negative capacity by family",
            "no-GT abstain/audit pool count",
            "shortcut-risk precheck plan",
        ],
        "do_not_do_next": [
            "Do not materialize rows before the inventory passes.",
            "Do not use no-GT as negative.",
            "Do not use validation/test labels.",
            "Do not modify H001 artifacts.",
            "Do not run learned smoke before schema/shortcut audit.",
        ],
        "success_condition": [
            "selected primary family/families for independent validity materialization",
            "minimum class mass estimate",
            "explicit target labels independent from same-G_e construction",
            "blocked fields and grouping contract",
            "next materialization plan or blocker decision",
        ],
    }


def build_decision(synthesis: dict[str, Any], inventories: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_independent_validity_target_plan_inputs"
    selected_path = SELECTED_PATH if not errors else "fix_inputs_before_independent_target_plan"
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "split": "train_only_target_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "family_capacity_table": family_capacity_rows(inventories),
        "input_synthesis_status": synthesis.get("status"),
        "next_plan_contract": next_plan_contract(),
        "next_todo": next_todo,
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "selected_target_contract": selected_target_contract(),
        "source_inventory_table": source_inventory_rows(inventories),
        "status": status,
        "target_option_table": target_option_rows(),
        "validation_errors": len(errors),
    }


def build_report(decision: dict[str, Any]) -> str:
    contract = decision["selected_target_contract"]
    lines = [
        "# H002 Independent Validity Target Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {decision['status']}",
        f"selected_path = {decision['selected_path']}",
        f"validation_errors = {decision['validation_errors']}",
        f"next_todo = {decision['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "The next H002 target should be GT-anchored and train-side. The two-family same-`G_e`",
        "results already prove the `C_e` mechanism in a controlled setting; the missing evidence is",
        "whether `C_e` remains useful when labels come from a source independent of the construction",
        "rule.",
        "",
        "Selected path:",
        "",
        "```text",
        decision["selected_path"],
        "```",
        "",
        "## Target Options",
        "",
        "| Option | Verdict | Main Risk | Next Action |",
        "| --- | --- | --- | --- |",
    ]
    for row in decision["target_option_table"]:
        lines.append(f"| `{row['option']}` | `{row['verdict']}` | {row['main_risk']} | `{row['next_action']}` |")

    lines.extend(
        [
            "",
            "## Family Capacity Snapshot",
            "",
            "| Family | Predicates | GT Count | Role | Decision |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in decision["family_capacity_table"]:
        lines.append(
            f"| `{row['family']}` | {row['predicate_counts']} | `{row['gt_count']}` | "
            f"`{row['target_role']}` | `{row['decision']}` |"
        )

    lines.extend(
        [
            "",
            "## Selected Target Contract",
            "",
            "```text",
            f"target_name = {contract['target_name']}",
            f"split_policy = {contract['split_policy']}",
            "primary_families = relative_vertical, support_contact_pose_conditioned",
            "```",
            "",
            "Label policy:",
            "",
            "- `C_e` positive: GT predicate and geometry evidence are compatible.",
            "- `C_e` negative: matched counterfactual predicate or wrong-pair candidate is geometry-incompatible and not GT-supported.",
            "- `C_e` abstain: no-GT but geometry-supported, low coverage, or annotation-sparse case.",
            "- `p_obs` is an observability target, not a truth target.",
            "- `p_rel` can be tested only after the inventory shows enough observable accept/reject rows.",
            "",
            "Forbidden policy:",
            "",
            "- no-GT is not a negative label.",
            "- validation/test labels are not used.",
            "- hidden construction fields are not model input.",
            "- H001 artifacts are read-only.",
            "",
            "## Source Inventory Decision",
            "",
            "| Source | Decision | Role | Caveat |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in decision["source_inventory_table"]:
        lines.append(f"| `{row['source']}` | `{row['decision']}` | {row['role']} | {row['caveat']} |")

    lines.extend(
        [
            "",
            "## Next Plan Contract",
            "",
            "The next step should inventory the selected sources before any row materialization.",
            "",
            "Required outputs:",
            "",
        ]
    )
    for item in decision["next_plan_contract"]["outputs_required"]:
        lines.append(f"- {item}")
    lines.extend(["", "Success condition:", ""])
    for item in decision["next_plan_contract"]["success_condition"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only target plan.",
            "- No validation/test usage.",
            "- No learned model trained in this step.",
            "- No H001 artifact modification.",
            "- No paper-level evidence promotion.",
            "",
            "## Next",
            "",
            "```text",
            decision["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    synthesis = read_json(args.synthesis_dir / "summary.json")
    inventories = {
        "dsg_train": count_relationships(args.dsg_train),
        "open3dsg_train_relationships": count_relationships(args.open3dsg_train_relationships),
        "open3dsg_raw_dump": {
            "exists": args.open3dsg_raw_dump.exists(),
            "path": rel_path(args.open3dsg_raw_dump),
            "rows": count_jsonl(args.open3dsg_raw_dump),
        },
        "manual_labels": manual_label_inventory(args.manual_labels),
        "attachment_audit": attachment_audit_inventory(args.attachment_audit),
    }
    errors = validate_inputs(synthesis, inventories)
    decision = build_decision(synthesis, inventories, errors)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(output_dir / "selected_target_contract.json", decision["selected_target_contract"])
    write_json(output_dir / "next_plan_contract.json", decision["next_plan_contract"])
    write_csv(output_dir / "target_option_table.csv", decision["target_option_table"])
    write_csv(output_dir / "family_capacity_table.csv", decision["family_capacity_table"])
    write_csv(output_dir / "source_inventory_table.csv", decision["source_inventory_table"])
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(decision), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
