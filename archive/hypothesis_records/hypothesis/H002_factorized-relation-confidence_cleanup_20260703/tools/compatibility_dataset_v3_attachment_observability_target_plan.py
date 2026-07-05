#!/usr/bin/env python3
"""Plan R7 attachment observability-first targets for H002."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_ROUTE_MAP_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review"
)
DEFAULT_ROUTE_MANIFEST_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)
DEFAULT_POSITIVE_ANCHOR_INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"
DEFAULT_POSITIVE_ANCHOR_AUDIT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_target_independence_audit_v1"
DEFAULT_PACKET_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_target_plan"

EXPECTED_ROUTE_MAP_STATUS = "h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_ready"
EXPECTED_ROUTE_MAP_NEXT = "compatibility_dataset_v3_attachment_observability_target_plan"
EXPECTED_ROUTE_MANIFEST_STATUS = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready"
EXPECTED_INGESTION_STATUS = "h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk"
EXPECTED_AUDIT_STATUS = "h002_attachment_independent_positive_anchor_target_independence_audit_blocked_shortcut_risk"
EXPECTED_PACKET_STATUS = "h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_target_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_attachment_observability_target_plan_ready_for_source_inventory"
STATUS_ERRORS = "h002_compatibility_dataset_v3_attachment_observability_target_plan_input_errors"
SELECTED_PATH = "plan_r7_attachment_observability_first_source_inventory_before_materialization"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_source_inventory"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-map-dir", type=Path, default=DEFAULT_ROUTE_MAP_DIR)
    parser.add_argument("--route-manifest-dir", type=Path, default=DEFAULT_ROUTE_MANIFEST_DIR)
    parser.add_argument("--positive-anchor-ingestion-dir", type=Path, default=DEFAULT_POSITIVE_ANCHOR_INGESTION_DIR)
    parser.add_argument("--positive-anchor-audit-dir", type=Path, default=DEFAULT_POSITIVE_ANCHOR_AUDIT_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
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


def validate_inputs(
    route_map: dict[str, Any],
    route_manifest: dict[str, Any],
    ingestion: dict[str, Any],
    audit: dict[str, Any],
    packet: dict[str, Any],
    route_rows: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "route_map": (route_map, EXPECTED_ROUTE_MAP_STATUS),
        "route_manifest": (route_manifest, EXPECTED_ROUTE_MANIFEST_STATUS),
        "positive_anchor_ingestion": (ingestion, EXPECTED_INGESTION_STATUS),
        "positive_anchor_audit": (audit, EXPECTED_AUDIT_STATUS),
        "packet_materialization": (packet, EXPECTED_PACKET_STATUS),
    }
    for name, (summary, status) in expected.items():
        if summary.get("status") != status:
            errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
        if summary.get("validation_errors", 0) not in (0, None):
            errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
        if read_jsonl(roots[name] / "validation_errors.jsonl"):
            errors.append({"input": name, "error_type": "validation_error_rows_present"})

    if route_map.get("next_todo") != EXPECTED_ROUTE_MAP_NEXT:
        errors.append({"input": "route_map", "error_type": "unexpected_next_todo", "actual": route_map.get("next_todo")})
    if route_map.get("next_active_route") != "attachment_observability":
        errors.append({"input": "route_map", "error_type": "attachment_not_next_active", "actual": route_map.get("next_active_route")})
    r6 = route_map.get("r6_decision", {})
    if r6.get("status") != "diagnostic_frozen_not_main_factorized_success":
        errors.append({"input": "route_map", "error_type": "r6_not_diagnostic_frozen", "actual": r6})

    route_by_id = {row.get("route_id"): row for row in route_rows}
    r7 = route_by_id.get("R7", {})
    if r7.get("route_type") != "observability_aware_route":
        errors.append({"input": "route_manifest", "error_type": "r7_route_type_mismatch", "actual": r7.get("route_type")})
    if r7.get("relations") != "attached to; hanging on; connected to":
        errors.append({"input": "route_manifest", "error_type": "r7_relations_mismatch", "actual": r7.get("relations")})
    if r7.get("target_axis") != "observability_then_reliability":
        errors.append({"input": "route_manifest", "error_type": "r7_target_axis_mismatch", "actual": r7.get("target_axis")})

    ingestion_boundary = ingestion.get("boundary", {})
    for key in ["posterior_smoke_allowed", "paper_evidence_allowed", "mesh_as_model_input", "multi_view_as_model_input"]:
        if ingestion_boundary.get(key) is not False:
            errors.append({"input": "positive_anchor_ingestion", "error_type": "boundary_not_false", "key": key})
    packet_boundary = packet.get("boundary", {})
    if packet_boundary.get("multi_view_or_mesh_as_audit_evidence") is not True:
        errors.append({"input": "packet_materialization", "error_type": "packet_audit_evidence_boundary_missing"})
    audit_counts = audit.get("counts", {})
    if audit_counts.get("strict_clear_slices_total") != 0:
        errors.append({"input": "positive_anchor_audit", "error_type": "expected_no_strict_clear_slices"})
    return errors


def predicate_policy() -> list[dict[str, Any]]:
    return [
        {
            "predicate": "attached to",
            "route_role": "primary_observability_then_reliability",
            "p_obs_positive": "pair has visible/mesh/point evidence that can decide physical attachment or mounted contact",
            "p_obs_negative": "attachment surface, endpoint identity, or pair visibility is missing/ambiguous",
            "p_rel_positive_when_observable": "clear physical attachment, mounted fixture relation, or stable contact beyond mere proximity/support",
            "p_rel_negative_when_observable": "near/contact/support relation without attachment, floor/support confound, or separated pair",
            "abstain_reasons": "occluded contact surface; generic endpoint labels; same-label ambiguity; insufficient mesh/multiview evidence",
            "notes": "Do not use source score/rank or previous proxy role as model input.",
        },
        {
            "predicate": "hanging on",
            "route_role": "primary_observability_then_reliability",
            "p_obs_positive": "subject/object and potential hanging anchor are visible or mesh/point evidence exposes suspension/contact",
            "p_obs_negative": "anchor/contact point is missing, occluded, or cannot be distinguished from floor/support contact",
            "p_rel_positive_when_observable": "subject is plausibly suspended or mounted from the object/anchor with vertical/hanging geometry",
            "p_rel_negative_when_observable": "subject is on floor/support surface, no anchor exists, or relation is only proximity/overlap",
            "abstain_reasons": "anchor not visible; mesh contact incomplete; object class supports multiple interpretations",
            "notes": "Hanging requires orientation/anchor evidence, not just near-contact.",
        },
        {
            "predicate": "connected to",
            "route_role": "diagnostic_observability_then_topology",
            "p_obs_positive": "physical connection, cable/pipe/topology, or functional connector evidence is visible or represented in mesh/context",
            "p_obs_negative": "connection type is functional/topological but not visible in current evidence",
            "p_rel_positive_when_observable": "only if physical/topological connection evidence is explicit",
            "p_rel_negative_when_observable": "near/overlap without connection, or disconnected object pair",
            "abstain_reasons": "functional connection ambiguity; topology not represented; cable/connector not visible",
            "notes": "Keep connected-to diagnostic until topology/functional evidence schema is defined.",
        },
    ]


def evidence_blocks() -> list[dict[str, Any]]:
    return [
        {
            "block": "T_e",
            "role": "semantic content",
            "allowed_fields": "predicate text/label; subject/object class/family; relation family",
            "forbidden_fields": "source score; source rank; proxy role; query id; GT match; old construction labels",
            "used_for": "predicate-conditioned compatibility and route selection",
        },
        {
            "block": "Z_e",
            "role": "source confidence",
            "allowed_fields": "source score/rank only for final diagnostic or final reliability ablation",
            "forbidden_fields": "C_e compatibility input; p_obs construction; audit label generation",
            "used_for": "optional source baseline/control after target independence is audited",
        },
        {
            "block": "G_e_attachment",
            "role": "predicate-independent physical evidence",
            "allowed_fields": (
                "pair point/contact features; surface/contact area; mesh contact/topology; distance/overlap; "
                "anchor geometry; vertical suspension/pose; normal/orientation evidence"
            ),
            "forbidden_fields": "predicate-specific labels; source/rank; visual audit decision; construction proxy",
            "used_for": "C_e when p_obs is sufficient",
        },
        {
            "block": "Q_e_observability",
            "role": "evidence quality and decidability",
            "allowed_fields": (
                "same-frame visibility; subject/object/pair crop availability; point count; mesh completeness; "
                "occlusion; endpoint identity confidence; visual-mesh disagreement; functional/topology ambiguity"
            ),
            "forbidden_fields": "accept/reject label; source score/rank; proxy role",
            "used_for": "p_obs and selective abstention before p_rel",
        },
        {
            "block": "C_e",
            "role": "predicate-geometry compatibility",
            "allowed_fields": "T_e x G_e_attachment only when p_obs is sufficient",
            "forbidden_fields": "Z_e; construction bucket; hidden proxy; packet id; review label",
            "used_for": "p_rel on observable rows only",
        },
    ]


def target_contract() -> list[dict[str, Any]]:
    return [
        {
            "target": "p_obs",
            "label_space": "observable_decidable; unobservable_abstain; topology_or_functional_uncertain",
            "positive_definition": "available visual/mesh/point evidence is sufficient to decide the relation",
            "negative_definition": "needed evidence is missing, occluded, incomplete, or endpoint identity is unresolved",
            "primary_metric": "AUROC/F1 for observable vs abstain plus abstain precision",
            "use": "first-head/selective decision",
        },
        {
            "target": "p_rel_observable",
            "label_space": "observable_accept; observable_reject",
            "positive_definition": "relation is reliable given observable evidence",
            "negative_definition": "relation is contradicted by observable evidence",
            "primary_metric": "AUROC/F1 on p_obs-positive rows only",
            "use": "second-head relation reliability; blocked until p_obs schema and shortcut audit pass",
        },
        {
            "target": "multiclass_route_label",
            "label_space": "observable_accept; observable_reject; unobservable_abstain; functional_or_topology_uncertain",
            "positive_definition": "native route state for audit and error taxonomy",
            "negative_definition": "not a binary target",
            "primary_metric": "macro-F1 and per-class confusion for diagnostic review",
            "use": "diagnostic only until class balance and independence pass",
        },
        {
            "target": "C_e_attachment",
            "label_space": "compatible; incompatible; abstain",
            "positive_definition": "T_e is compatible with predicate-independent G_e_attachment when p_obs is sufficient",
            "negative_definition": "hard negative with matched predicate/class/source strata but incompatible G_e",
            "primary_metric": "paired margin/AUROC with wrong-T, shuffled-G, shuffled-view, and wrong-pair controls",
            "use": "candidate learned compatibility target after source inventory and schema audit",
        },
    ]


def model_view_contract() -> list[dict[str, Any]]:
    return [
        {
            "view": "p_obs_Q_only",
            "allowed_blocks": "Q_e_observability",
            "purpose": "test whether evidence availability predicts decidability",
            "blocked_until": "source inventory materializes Q_e fields",
        },
        {
            "view": "G_only",
            "allowed_blocks": "G_e_attachment",
            "purpose": "geometry-only control on observable rows",
            "blocked_until": "G_e source inventory and schema audit",
        },
        {
            "view": "T_only",
            "allowed_blocks": "T_e",
            "purpose": "semantic shortcut control",
            "blocked_until": "target materialization",
        },
        {
            "view": "T_x_G_compatibility",
            "allowed_blocks": "T_e; G_e_attachment",
            "purpose": "C_e attachment compatibility when p_obs is sufficient",
            "blocked_until": "p_obs target passes shortcut audit",
        },
        {
            "view": "factorized_two_head",
            "allowed_blocks": "T_e; G_e_attachment; Q_e_observability; optional Z_e final baseline only",
            "purpose": "two-head p_obs then p_rel decision",
            "blocked_until": "independent target and controls pass",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    fields = [
        "source_score",
        "source_rank",
        "source_rank_band",
        "query_id_hidden",
        "selection_proxy_role_hidden",
        "cell_id_hidden",
        "packet_id",
        "review_relation_reliability",
        "review_geometry_support",
        "review_coverage",
        "review_uncertainty",
        "gt_match_status",
        "p_geom_valid",
        "construction_proxy_label",
        "visible_pair_id",
        "scan_id",
        "object_instance_id",
        "subject_instance_id",
    ]
    return [
        {
            "field": field,
            "blocked_from": "model_safe_C_e_p_obs_p_rel_inputs",
            "reason": "shortcut/leakage/provenance field; allowed only in hidden audit or control manifest",
        }
        for field in fields
    ]


def source_reuse_inventory(ingestion: dict[str, Any], audit: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, Any]]:
    ingestion_counts = ingestion.get("counts", {})
    audit_counts = audit.get("counts", {})
    packet_counts = packet.get("counts", {})
    return [
        {
            "source": "attachment_independent_positive_anchor_label_ingestion_v1",
            "status": ingestion.get("status"),
            "rows": ingestion_counts.get("rows"),
            "predicate_counts": json.dumps(ingestion_counts.get("predicate_label", {}), sort_keys=True),
            "label_counts": json.dumps(ingestion_counts.get("review_relation_reliability", {}), sort_keys=True),
            "role": "diagnostic label/source-count reference only",
            "limitation": "shortcut risk; not direct training target",
        },
        {
            "source": "attachment_independent_positive_anchor_target_independence_audit_v1",
            "status": audit.get("status"),
            "rows": audit_counts.get("rows"),
            "strict_clear_slices": audit_counts.get("strict_clear_slices_total"),
            "diagnostic_clear_slices": audit_counts.get("diagnostic_clear_slices_total"),
            "role": "blocker evidence motivating observability-first redesign",
            "limitation": "previous binary target not independently identifiable",
        },
        {
            "source": "attachment_independent_positive_anchor_packet_materialization_v1",
            "status": packet.get("status"),
            "rows": packet_counts.get("packet_rows"),
            "packet_status": json.dumps(packet_counts.get("packet_status_counts", {}), sort_keys=True),
            "role": "potential packet/evidence source for R7 source inventory",
            "limitation": "packets are audit evidence until Q_e/G_e model-safe schema is materialized",
        },
    ]


def gate_plan() -> list[dict[str, Any]]:
    return [
        {
            "gate": "G0_no_materialization_in_plan",
            "requirement": "target plan writes schema and route contract only",
            "threshold": "no candidate rows emitted",
        },
        {
            "gate": "G1_source_inventory",
            "requirement": "count available pair point, mesh, visual packet, and topology/functional evidence for R7",
            "threshold": "predicate-level counts for attached/hanging/connected and missing-evidence rates",
        },
        {
            "gate": "G2_p_obs_schema",
            "requirement": "Q_e fields separate observability from accept/reject labels",
            "threshold": "model-safe Q_e excludes review labels and proxy fields",
        },
        {
            "gate": "G3_p_rel_only_when_observable",
            "requirement": "p_rel rows are emitted only for p_obs-positive rows",
            "threshold": "no p_rel target on unobservable/functional-uncertain rows",
        },
        {
            "gate": "G4_shortcut_audit",
            "requirement": "predicate/class/query/packet/source/rank fields cannot solve p_obs or p_rel alone",
            "threshold": "no high-risk model-safe probe before smoke",
        },
        {
            "gate": "G5_controls",
            "requirement": "wrong-pair, shuffled-view, shuffled-G, wrong-T, no-view controls are predeclared",
            "threshold": "controls materialized before learned smoke",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "next_todo": NEXT_TODO,
            "action": "Run R7 source inventory over existing attachment candidates, packet assets, mesh/point sources, and review labels.",
            "blocked": False,
        },
        {
            "order": 2,
            "next_todo": "compatibility_dataset_v3_attachment_observability_materialization_plan",
            "action": "Only if source inventory passes, freeze row quota and model-safe/hidden output schema.",
            "blocked": "requires source inventory",
        },
        {
            "order": 3,
            "next_todo": "compatibility_dataset_v3_attachment_observability_schema_shortcut_audit",
            "action": "Audit p_obs and observable p_rel targets before any learned smoke.",
            "blocked": "requires materialized rows",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    predicate_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Attachment Observability Target Plan",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Decision",
        "",
        "R7 `attached to` / `hanging on` / `connected to`를 observability-first route로 계획한다.",
        "즉, relation reliability를 바로 binary target으로 만들지 않고, `Q_e`/`p_obs`가 먼저 판단 가능성을 결정한다.",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Predicate Policy",
        "",
        "| Predicate | Role | p_obs Positive | p_rel Positive When Observable |",
        "| --- | --- | --- | --- |",
    ]
    for row in predicate_rows:
        lines.append(
            f"| `{row['predicate']}` | {row['route_role']} | {row['p_obs_positive']} | {row['p_rel_positive_when_observable']} |"
        )
    lines.extend(["", "## Target Contract", ""])
    for row in target_rows:
        lines.append(f"- `{row['target']}`: {row['label_space']} / use={row['use']}")
    lines.extend(["", "## Existing Source Reuse", ""])
    for row in source_rows:
        lines.append(f"- `{row['source']}`: role={row['role']} / limitation={row['limitation']}")
    lines.extend(["", "## Gates", ""])
    for row in gate_rows:
        lines.append(f"- `{row['gate']}`: {row['requirement']} / threshold={row['threshold']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No row materialization in this step.",
            "- No learned smoke in this step.",
            "- Multi-view/mesh packets remain audit/source-inventory evidence until model-safe `G_e`/`Q_e` fields are defined.",
            "- `connected to` remains diagnostic until physical/topological/functional connection evidence is explicit.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    roots = {
        "route_map": args.route_map_dir,
        "route_manifest": args.route_manifest_dir,
        "positive_anchor_ingestion": args.positive_anchor_ingestion_dir,
        "positive_anchor_audit": args.positive_anchor_audit_dir,
        "packet_materialization": args.packet_dir,
    }
    route_map = read_json(args.route_map_dir / "summary.json")
    route_manifest = read_json(args.route_manifest_dir / "summary.json")
    ingestion = read_json(args.positive_anchor_ingestion_dir / "summary.json")
    audit = read_json(args.positive_anchor_audit_dir / "summary.json")
    packet = read_json(args.packet_dir / "summary.json")
    route_rows = read_csv(args.route_manifest_dir / "route_target_manifest.csv")

    errors = validate_inputs(route_map, route_manifest, ingestion, audit, packet, route_rows, roots)
    status = STATUS_ERRORS if errors else STATUS_READY

    predicate_rows = [] if errors else predicate_policy()
    evidence_rows = [] if errors else evidence_blocks()
    target_rows = [] if errors else target_contract()
    model_rows = [] if errors else model_view_contract()
    blocked_rows = [] if errors else blocked_fields()
    source_rows = [] if errors else source_reuse_inventory(ingestion, audit, packet)
    gate_rows = [] if errors else gate_plan()
    next_rows = [] if errors else next_steps()

    ingestion_counts = ingestion.get("counts", {})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "route_map_dir": rel_path(args.route_map_dir),
            "route_manifest_dir": rel_path(args.route_manifest_dir),
            "positive_anchor_ingestion_dir": rel_path(args.positive_anchor_ingestion_dir),
            "positive_anchor_audit_dir": rel_path(args.positive_anchor_audit_dir),
            "packet_dir": rel_path(args.packet_dir),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "predicate_policy": rel_path(args.output_dir / "predicate_policy.csv"),
            "evidence_blocks": rel_path(args.output_dir / "evidence_blocks.csv"),
            "target_contract": rel_path(args.output_dir / "target_contract.csv"),
            "model_view_contract": rel_path(args.output_dir / "model_view_contract.csv"),
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
            "source_reuse_inventory": rel_path(args.output_dir / "source_reuse_inventory.csv"),
            "gate_plan": rel_path(args.output_dir / "gate_plan.csv"),
            "next_steps": rel_path(args.output_dir / "next_steps.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "route": {
            "route_id": "R7",
            "family": "attachment_observability",
            "relations": ["attached to", "hanging on", "connected to"],
            "target_axis": "observability_then_reliability",
            "selected_next": True,
        },
        "existing_attachment_label_snapshot": {
            "rows": ingestion_counts.get("rows"),
            "predicate_counts": ingestion_counts.get("predicate_label"),
            "review_relation_reliability": ingestion_counts.get("review_relation_reliability"),
            "p_obs_target": ingestion_counts.get("p_obs_target"),
            "primary_binary_target": ingestion_counts.get("primary_binary_target"),
            "shortcut_risk_flags": ingestion_counts.get("quick_probe_risk_flags"),
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "posterior_smoke_allowed": False,
            "runs_model": False,
            "test_usage": False,
            "validation_usage": False,
            "mesh_as_model_input": False,
            "multi_view_as_model_input": False,
            "mesh_or_multiview_as_source_inventory_evidence": True,
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "predicate_policy.csv", predicate_rows)
    write_csv(args.output_dir / "evidence_blocks.csv", evidence_rows)
    write_csv(args.output_dir / "target_contract.csv", target_rows)
    write_csv(args.output_dir / "model_view_contract.csv", model_rows)
    write_csv(args.output_dir / "blocked_fields.csv", blocked_rows)
    write_csv(args.output_dir / "source_reuse_inventory.csv", source_rows)
    write_csv(args.output_dir / "gate_plan.csv", gate_rows)
    write_csv(args.output_dir / "next_steps.csv", next_rows)
    if not errors:
        write_report(args.output_dir / "report.md", summary, predicate_rows, target_rows, source_rows, gate_rows)
    else:
        (args.output_dir / "report.md").write_text(
            "# Attachment Observability Target Plan\n\nInput validation failed; see `validation_errors.jsonl`.\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
