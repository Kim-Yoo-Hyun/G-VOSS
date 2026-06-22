#!/usr/bin/env python3
"""Design the H002 v6 uncertainty-aware reliability target."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_fill_codex_proxy_user_requested"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_target_independence_audit_codex_proxy_user_requested"
DEFAULT_PATH_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_path_decision_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_target_design_codex_proxy_user_requested"

NEXT_TODO = "reliability_target_v6_uncertainty_aware_seed_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-dir", type=Path, default=DEFAULT_FILL_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--path-dir", type=Path, default=DEFAULT_PATH_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


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
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def v6_state(row: dict[str, str]) -> str:
    value = row["relation_reliability_v5"]
    if value == "reliable":
        return "accept_reliable"
    if value == "unreliable":
        return "reject_unreliable"
    if value == "uncertain":
        return "abstain_uncertain"
    return "unknown"


def v6_subtype(row: dict[str, str]) -> str:
    state = v6_state(row)
    primary = row["primary_reason_v5"]
    uncertainty = row["uncertainty_reason_v5"]
    if state == "accept_reliable":
        return "confident_geometric_support"
    if state == "reject_unreliable" and primary == "geometric_contradiction":
        return "geometry_contradiction"
    if state == "reject_unreliable" and primary == "trivial_room_surface_or_structure":
        return "trivial_or_nonrelation"
    if state == "abstain_uncertain" and primary == "endpoint_identity_issue":
        return "endpoint_identity_uncertain"
    if state == "abstain_uncertain" and uncertainty == "predicate_definition_ambiguous":
        return "predicate_definition_ambiguous"
    if state == "abstain_uncertain" and uncertainty == "occlusion_or_view_limit":
        return "view_or_mesh_limited"
    if state == "abstain_uncertain" and uncertainty == "object_segmentation_issue":
        return "object_segmentation_issue"
    if state == "abstain_uncertain" and primary == "insufficient_evidence":
        return "insufficient_evidence"
    return "other"


def geometry_state(row: dict[str, str]) -> str:
    mapping = {
        "supports": "geometry_supports",
        "contradicts": "geometry_contradicts",
        "ambiguous": "geometry_ambiguous",
        "not_evaluable": "geometry_not_evaluable",
    }
    return mapping.get(row["geometry_support_v5"], "geometry_unknown")


def usefulness_state(row: dict[str, str]) -> str:
    value = row["relation_usefulness_v5"]
    if value == "useful_nontrivial":
        return "useful_nontrivial"
    if value in {"trivial_or_redundant", "not_a_relation"}:
        return "not_useful_or_not_relation"
    if value == "uncertain":
        return "usefulness_uncertain"
    return "usefulness_unknown"


def seed_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        output.append(
            {
                "schema_version": "h002_reliability_target_v6_uncertainty_aware_design_seed_v1",
                "blind_review_id": row["blind_review_id"],
                "scan_id": row["scan_id"],
                "scene_context_id": row["scene_context_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "subject_label": row["subject_label"],
                "object_label": row["object_label"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "v6_reliability_state": v6_state(row),
                "v6_reliability_subtype": v6_subtype(row),
                "v6_geometry_state_aux": geometry_state(row),
                "v6_usefulness_state_aux": usefulness_state(row),
                "v5_relation_reliability": row["relation_reliability_v5"],
                "v5_geometry_support": row["geometry_support_v5"],
                "v5_relation_usefulness": row["relation_usefulness_v5"],
                "v5_primary_reason": row["primary_reason_v5"],
                "v5_uncertainty_reason": row["uncertainty_reason_v5"],
                "evidence_packet_status": row["evidence_packet_status"],
                "packet_gap_decision": row["packet_gap_decision"],
                "target_use": "design_seed_only",
                "posterior_training_allowed": False,
                "paper_evidence_allowed": False,
                "review_fields_not_model_input": True,
            }
        )
    return output


def inventory_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    views = {
        "v6_state": lambda row: (row["v6_reliability_state"],),
        "v6_state_x_subtype": lambda row: (row["v6_reliability_state"], row["v6_reliability_subtype"]),
        "v6_state_x_geometry_aux": lambda row: (row["v6_reliability_state"], row["v6_geometry_state_aux"]),
        "v6_state_x_usefulness_aux": lambda row: (row["v6_reliability_state"], row["v6_usefulness_state_aux"]),
        "v6_state_x_family": lambda row: (row["v6_reliability_state"], row["predicate_family"]),
        "v6_state_x_predicate": lambda row: (row["v6_reliability_state"], row["predicate_label"]),
        "v6_state_x_packet_status": lambda row: (row["v6_reliability_state"], row["evidence_packet_status"]),
        "v6_state_x_packet_gap": lambda row: (row["v6_reliability_state"], row["packet_gap_decision"]),
    }
    output: list[dict[str, Any]] = []
    for view, fn in views.items():
        counts = Counter(fn(row) for row in rows)
        for key, count in sorted(counts.items()):
            output.append(
                {
                    "inventory_view": view,
                    "key_1": key[0] if len(key) > 0 else "",
                    "key_2": key[1] if len(key) > 1 else "",
                    "count": count,
                }
            )
    return output


def target_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_uncertainty_aware_schema_v1",
        "selected_primary_target": "nominal_multiclass_reliability_with_abstention",
        "primary_target_name": "relation_reliability_state_v6",
        "primary_states": {
            "accept_reliable": {
                "meaning": "edge is sufficiently reliable for downstream graph use under available evidence",
                "derived_from_v5": "relation_reliability_v5 == reliable",
                "model_role": "positive reliability state",
            },
            "reject_unreliable": {
                "meaning": "edge should not be trusted as a relation under available evidence",
                "derived_from_v5": "relation_reliability_v5 == unreliable",
                "model_role": "negative reliability state",
            },
            "abstain_uncertain": {
                "meaning": "available evidence is insufficient or ambiguous; the system should abstain rather than force reliable/unreliable",
                "derived_from_v5": "relation_reliability_v5 == uncertain",
                "model_role": "uncertainty/abstention state, not discarded supervision",
            },
        },
        "subtype_axis": {
            "name": "relation_reliability_subtype_v6",
            "role": "diagnostic and optional auxiliary supervision, not the main class metric until mass is sufficient",
            "states": [
                "confident_geometric_support",
                "geometry_contradiction",
                "trivial_or_nonrelation",
                "endpoint_identity_uncertain",
                "predicate_definition_ambiguous",
                "view_or_mesh_limited",
                "object_segmentation_issue",
                "insufficient_evidence",
                "other",
            ],
        },
        "auxiliary_targets": {
            "geometry_support_state_v6": {
                "states": ["geometry_supports", "geometry_contradicts", "geometry_ambiguous", "geometry_not_evaluable"],
                "role": "auxiliary evidence-axis target; not a replacement for relation reliability",
            },
            "relation_usefulness_state_v6": {
                "states": ["useful_nontrivial", "not_useful_or_not_relation", "usefulness_uncertain"],
                "role": "auxiliary evidence-axis target; not a replacement for relation reliability",
            },
        },
        "rejected_target_forms": {
            "pure_binary_reliable_vs_unreliable": "rejects/throws away the dominant uncertain evidence state",
            "geometry_support_as_main_target": "collapses relation reliability into geometry validity",
            "relation_usefulness_as_main_target": "does not solve object/cell shortcut risk",
            "ordinal_reliable_uncertain_unreliable": "uncertain is not guaranteed to lie between reliable and unreliable",
            "direct_pair_ranking": "current v5 has 0/36 direct reliable/unreliable pair contrasts",
        },
    }


def input_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_input_contract_v1",
        "posterior_candidate_inputs": {
            "semantic_evidence": [
                "semantic_score_raw",
                "semantic_score_norm",
                "semantic_rank as continuous or monotonic transformed feature",
            ],
            "geometry_evidence": [
                "p_geom_valid as geometry-only scalar baseline",
                "relation-family-specific continuous residuals when available",
                "coverage-normalized geometry evidence when available",
            ],
            "coverage_uncertainty_evidence": [
                "geometry coverage/missingness indicators",
                "packet/evidence availability indicators that are deployable without audit packet content",
                "uncertainty proxies derived from deployable evidence, not from review labels",
            ],
            "relation_conditioning": [
                "predicate_family as typed relation-family conditioning with group-aware evaluation",
                "predicate_label only if family/predicate controls are predeclared",
            ],
            "object_quality_evidence": [
                "numeric object/instance confidence if available",
                "do not use subject/object class labels as direct reliability shortcuts",
            ],
        },
        "forbidden_inputs": [
            "v5 or v6 review fields",
            "relation_reliability labels",
            "geometry_support labels",
            "relation_usefulness labels",
            "primary_reason or uncertainty_reason labels",
            "cell_contrast_pair_id_hidden",
            "cell_contrast_key_hidden",
            "cell_contrast_role_hidden",
            "subject_object_family_cell_hidden",
            "object_family_cell_hidden",
            "subject_label and object_label as main posterior features",
            "geometry_status_hidden",
            "label_match_status_hidden",
            "rank_band_hidden as sampling bucket",
            "source_queue_hidden as target-construction role",
            "audit packet paths",
            "multi-view content before explicit future promotion",
        ],
        "boundary": {
            "multi_view_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "review_fields_as_model_input": False,
            "validation_usage": False,
            "test_usage": False,
        },
    }


def independence_gate_plan() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_independence_gate_plan_v1",
        "gate_order": [
            "seed_inventory_audit",
            "multiclass_target_independence_audit",
            "source_feature_join_contract",
            "train_only_posterior_smoke_only_if_gates_pass",
        ],
        "class_mass_gates": {
            "diagnostic_seed_min_per_state": 10,
            "posterior_smoke_min_per_state": 20,
            "paper_claim_min_per_state": "requires independent human-confirmed labels; not satisfied by current Codex proxy labels",
            "current_v5_seed_state_counts": {
                "accept_reliable": 19,
                "reject_unreliable": 12,
                "abstain_uncertain": 41,
            },
        },
        "shortcut_audit_groups": [
            "cell_contrast_pair_id_hidden",
            "cell_contrast_key_hidden",
            "subject_object_family_cell_hidden",
            "object_family_cell_hidden",
            "subject_label",
            "object_label",
            "predicate_family",
            "predicate_label",
            "rank_band_hidden",
            "source_queue_hidden",
            "geometry_status_hidden",
            "packet source and packet gap",
        ],
        "risk_metrics": [
            "multiclass normalized mutual information",
            "group majority improvement over global majority baseline",
            "per-state one-vs-rest majority shortcut",
            "leave-one-cell-out or group-heldout diagnostic when sample size permits",
        ],
        "posterior_reopen_conditions": [
            "all three primary states meet posterior_smoke_min_per_state or a predeclared class-weighted diagnostic exception is justified",
            "no forbidden group alone explains the target under the shortcut audit",
            "a nontrivial controlled slice remains after cell/pair/object-family grouping",
            "semantic and continuous geometry factors are available without review labels",
            "validation/test usage remains false",
        ],
        "blocked_conditions": [
            "target becomes predictable from pair/cell/object-family identity",
            "uncertain state collapses entirely to packet availability rather than relation ambiguity",
            "reliable/unreliable states remain below diagnostic class mass",
            "posterior requires subject/object class labels to work",
        ],
    }


def reuse_policy() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_v5_reuse_policy_v1",
        "v5_labels_allowed_use": [
            "design seed inventory",
            "failure-mode trace",
            "schema sanity check",
            "target-independence seed audit",
        ],
        "v5_labels_forbidden_use": [
            "paper metric evidence",
            "posterior performance claim",
            "validation or test tuning",
            "final human-confirmed annotation substitute",
        ],
        "current_status": "v5 labels are user-requested Codex proxy labels and remain hypothesis-stage only",
        "next_use": "convert v5 rows into v6 design-seed rows and audit multiclass shortcut risk before any model smoke",
    }


def option_matrix() -> list[dict[str, str]]:
    return [
        {
            "option": "pure_binary_reliability",
            "verdict": "reject",
            "reason": "discarded 41/72 uncertain rows and produced a sparse shortcut-prone target",
        },
        {
            "option": "nominal_multiclass_with_abstention",
            "verdict": "select_primary",
            "reason": "preserves the uncertainty axis without assuming uncertain is ordinally between reliable and unreliable",
        },
        {
            "option": "abstention_aware_binary",
            "verdict": "secondary",
            "reason": "can be evaluated after multiclass seed audit; uncertainty should not be silently dropped",
        },
        {
            "option": "multi_task_reliability_geometry_usefulness",
            "verdict": "select_auxiliary",
            "reason": "keeps geometry support and usefulness as evidence axes without replacing reliability",
        },
        {
            "option": "ordinal_reliability",
            "verdict": "reject_for_now",
            "reason": "uncertain can mean ambiguity, missing evidence, or segmentation issue, not a calibrated middle class",
        },
        {
            "option": "pairwise_ranking",
            "verdict": "reject_for_now",
            "reason": "current v5 has 0/36 direct reliable/unreliable pair contrasts",
        },
    ]


def failure_to_design_trace(fill_summary: dict[str, Any], audit_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rel = audit_summary["target_decisions"]["relation_reliability_v5_binary_target"]["original"]
    return [
        {
            "failure": "binary_target_sparsity",
            "evidence": {
                "binary_rows": rel["rows"],
                "positive": rel["positive"],
                "negative": rel["negative"],
                "uncertain_excluded": fill_summary["counts"]["relation_reliability_v5"]["uncertain"],
            },
            "design_response": "make abstain_uncertain a primary target state",
        },
        {
            "failure": "pair_contrast_absent",
            "evidence": audit_summary["pair_diagnostics"],
            "design_response": "do not select pairwise ranking as the next primary target",
        },
        {
            "failure": "cell_and_object_shortcuts",
            "evidence": {
                "cell_risks": rel["top_cell_contrast_design_risks"],
                "endpoint_object_risks": rel["top_endpoint_object_structure_risks"],
                "visible_object_risks": rel["top_visible_object_identity_risks"],
            },
            "design_response": "make cell/pair/object-family variables audit-only blockers and predeclare group-aware independence checks",
        },
        {
            "failure": "geometry_target_collapse",
            "evidence": fill_summary["counts"]["geometry_support_v5"],
            "design_response": "keep geometry support as auxiliary evidence-axis target, not main reliability",
        },
        {
            "failure": "usefulness_target_collapse",
            "evidence": fill_summary["counts"]["relation_usefulness_v5"],
            "design_response": "keep usefulness as auxiliary evidence-axis target, not main reliability",
        },
    ]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["seed_inventory_summary"]["state_counts"]
    lines = [
        "# H002 Reliability Target V6 Uncertainty-Aware Target Design",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only target design artifact.",
        "- No posterior is trained.",
        "- No new labels are filled.",
        "- No validation/test rows are used.",
        "- V5 labels are used only as design-seed inventory, not paper evidence.",
        "- Multi-view remains audit evidence only.",
        "- H001 artifacts are not modified.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Selected target form:",
        "",
        f"`{summary['target_schema']['selected_primary_target']}`",
        "",
        "## Seed Inventory",
        "",
        "| V6 State | Rows |",
        "| --- | ---: |",
    ]
    for state, count in sorted(counts.items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Option Matrix",
            "",
            "| Option | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary["option_matrix"]:
        lines.append(f"| `{row['option']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Design Gates",
            "",
            f"- Diagnostic seed min per state: `{summary['independence_gate_plan']['class_mass_gates']['diagnostic_seed_min_per_state']}`",
            f"- Posterior smoke min per state: `{summary['independence_gate_plan']['class_mass_gates']['posterior_smoke_min_per_state']}`",
            "- Group-aware shortcut audit must include pair/cell/object-family and visible object labels.",
            "- Posterior smoke stays blocked until the seed audit passes.",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    fill_dir = as_abs(args.fill_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    audit_dir = as_abs(args.audit_dir)
    path_dir = as_abs(args.path_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(fill_dir / "summary.json")
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    audit_summary = read_json(audit_dir / "summary.json")
    path_summary = read_json(path_dir / "summary.json")
    completed_rows = read_tsv(fill_dir / "completed_v5_cell_contrast_label_sheet_codex_proxy_user_requested.tsv")

    seeds = seed_rows(completed_rows)
    inventory = inventory_rows(seeds)
    schema = target_schema()
    contract = input_contract()
    gates = independence_gate_plan()
    reuse = reuse_policy()
    options = option_matrix()
    trace = failure_to_design_trace(fill_summary, audit_summary)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "target_schema": output_dir / "target_schema.json",
        "input_contract": output_dir / "input_contract.json",
        "independence_gate_plan": output_dir / "independence_gate_plan.json",
        "v5_reuse_policy": output_dir / "v5_reuse_policy.json",
        "option_matrix": output_dir / "option_matrix.json",
        "failure_to_design_trace": output_dir / "failure_to_design_trace.json",
        "seed_labels": output_dir / "seed_labels_v6_design_only.jsonl",
        "seed_inventory": output_dir / "seed_state_inventory.csv",
    }

    state_counts = Counter(row["v6_reliability_state"] for row in seeds)
    subtype_counts = Counter(row["v6_reliability_subtype"] for row in seeds)
    status = "h002_reliability_target_v6_uncertainty_aware_target_design_ready_for_seed_audit"
    decision = (
        "Select a nominal multiclass reliability target with an explicit abstain_uncertain state. "
        "Keep geometry support and relation usefulness as auxiliary evidence-axis targets. "
        "Do not train posterior or fill new labels until the v6 seed audit tests class mass and "
        "cell/pair/object-family shortcut risk."
    )

    summary = {
        "schema_version": "h002_reliability_target_v6_uncertainty_aware_target_design_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "next_todo": NEXT_TODO,
        "input_paths": {
            "fill_summary": rel_path(fill_dir / "summary.json"),
            "completed_v5_sheet": rel_path(fill_dir / "completed_v5_cell_contrast_label_sheet_codex_proxy_user_requested.tsv"),
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "path_decision_summary": rel_path(path_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "upstream_status": {
            "fill": fill_summary.get("status"),
            "ingestion": ingestion_summary.get("status"),
            "audit": audit_summary.get("status"),
            "path_decision": path_summary.get("status"),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_new_labels": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "v5_labels_are_design_seed_only": True,
        },
        "target_schema": schema,
        "input_contract": contract,
        "independence_gate_plan": gates,
        "v5_reuse_policy": reuse,
        "option_matrix": options,
        "failure_to_design_trace": trace,
        "seed_inventory_summary": {
            "rows": len(seeds),
            "state_counts": dict(sorted(state_counts.items())),
            "subtype_counts": dict(sorted(subtype_counts.items())),
            "v5_relation_reliability_counts": fill_summary["counts"]["relation_reliability_v5"],
            "v5_geometry_support_counts": fill_summary["counts"]["geometry_support_v5"],
            "v5_relation_usefulness_counts": fill_summary["counts"]["relation_usefulness_v5"],
        },
    }

    write_json(output_paths["target_schema"], schema)
    write_json(output_paths["input_contract"], contract)
    write_json(output_paths["independence_gate_plan"], gates)
    write_json(output_paths["v5_reuse_policy"], reuse)
    write_json(output_paths["option_matrix"], options)
    write_json(output_paths["failure_to_design_trace"], trace)
    write_jsonl(output_paths["seed_labels"], seeds)
    write_csv(output_paths["seed_inventory"], inventory)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["seed_inventory_summary"]["state_counts"]
    print(
        "status={status} selected={selected} accept={accept} reject={reject} abstain={abstain} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} "
        "test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            selected=summary["target_schema"]["selected_primary_target"],
            accept=counts.get("accept_reliable", 0),
            reject=counts.get("reject_unreliable", 0),
            abstain=counts.get("abstain_uncertain", 0),
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
