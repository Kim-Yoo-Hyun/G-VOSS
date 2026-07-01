#!/usr/bin/env python3
"""Plan model-safe R7 attachment observability materialization."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_source_inventory"
DEFAULT_INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"
DEFAULT_PACKET_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan"

EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan"
)
EXPECTED_SOURCE_NEXT = "compatibility_dataset_v3_attachment_observability_materialization_plan"
EXPECTED_INGESTION_STATUS = "h002_attachment_independent_positive_anchor_label_ingested_class_mass_pass_with_shortcut_risk"
EXPECTED_PACKET_STATUS = "h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_attachment_observability_materialization_plan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_attachment_observability_materialization_plan_input_errors"
SELECTED_PATH = "plan_primary_attached_hanging_gq_materialization_keep_connected_diagnostic"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_materialization"

PRIMARY_PREDICATES = ("attached to", "hanging on")
DIAGNOSTIC_PREDICATES = ("connected to",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(
    source_summary: dict[str, Any],
    source_errors: list[dict[str, Any]],
    ingestion_summary: dict[str, Any],
    packet_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"input": "source_inventory", "error_type": "unexpected_status", "actual": source_summary.get("status")})
    if source_summary.get("next_todo") != EXPECTED_SOURCE_NEXT:
        errors.append({"input": "source_inventory", "error_type": "unexpected_next_todo", "actual": source_summary.get("next_todo")})
    if source_summary.get("validation_errors") != 0:
        errors.append({"input": "source_inventory", "error_type": "validation_errors_present", "actual": source_summary.get("validation_errors")})
    if source_errors:
        errors.append({"input": "source_inventory_validation_errors", "error_type": "rows_present", "rows": len(source_errors)})
    if ingestion_summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"input": "label_ingestion", "error_type": "unexpected_status", "actual": ingestion_summary.get("status")})
    if packet_summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"input": "packet_materialization", "error_type": "unexpected_status", "actual": packet_summary.get("status")})

    for source_name, payload in [
        ("source_inventory", source_summary),
        ("label_ingestion", ingestion_summary),
        ("packet_materialization", packet_summary),
    ]:
        boundary = payload.get("boundary", {})
        for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed", "posterior_smoke_allowed"]:
            if boundary.get(key) is not False:
                errors.append({"input": source_name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
        for key in ["multi_view_as_model_input", "mesh_as_model_input"]:
            if boundary.get(key) is not False:
                errors.append({"input": source_name, "error_type": "model_input_boundary_not_false", "key": key, "actual": boundary.get(key)})

    route_rows = source_summary.get("route_readiness", [])
    route_by_pred = {row.get("predicate_label"): row for row in route_rows}
    for predicate in PRIMARY_PREDICATES:
        if route_by_pred.get(predicate, {}).get("decision") != "ready_for_observability_materialization_plan":
            errors.append({"input": "source_inventory", "error_type": "primary_route_not_ready", "predicate": predicate})
    if route_by_pred.get("connected to", {}).get("decision") != "diagnostic_only_until_explicit_topology_or_functional_evidence":
        errors.append({"input": "source_inventory", "error_type": "connected_route_not_diagnostic"})
    return errors


def distribution_snapshot(ingestion_summary: dict[str, Any]) -> dict[str, Any]:
    counts = ingestion_summary.get("counts", {})
    return {
        "rows": counts.get("rows"),
        "predicate_label": counts.get("predicate_label"),
        "p_obs_target": counts.get("p_obs_target"),
        "primary_binary_target": counts.get("primary_binary_target"),
        "review_relation_reliability": counts.get("review_relation_reliability"),
        "review_geometry_support": counts.get("review_geometry_support"),
        "review_uncertainty": counts.get("review_uncertainty"),
        "quick_probe_risk_flags": counts.get("quick_probe_risk_flags"),
    }


def row_quota_plan(source_summary: dict[str, Any], ingestion_summary: dict[str, Any]) -> list[dict[str, Any]]:
    route_by_pred = {row["predicate_label"]: row for row in source_summary.get("route_readiness", [])}
    counts = ingestion_summary.get("counts", {})
    primary_rows = sum(route_by_pred.get(pred, {}).get("packet_rows", 0) for pred in PRIMARY_PREDICATES)
    diagnostic_rows = route_by_pred.get("connected to", {}).get("packet_rows", 0)
    return [
        {
            "wave": "W1_primary_attachment_observability",
            "route_role": "primary_observability_then_reliability",
            "predicates": "attached to; hanging on",
            "planned_rows": primary_rows,
            "source_rows": "existing ready R7 packets",
            "target_axes": "p_obs; p_rel_observable; C_e_attachment after schema audit",
            "p_obs_available": f"observable {counts.get('p_obs_target', {}).get('1')} / abstain {counts.get('p_obs_target', {}).get('0')} across all R7; primary subset is checked in materialization",
            "p_rel_available": f"accept {counts.get('primary_binary_target', {}).get('1')} / reject {counts.get('primary_binary_target', {}).get('0')} / abstain {counts.get('abstain_rows')}",
            "use_now": "source row and hidden-target materialization only; learned smoke blocked until schema shortcut audit",
            "caveat": "p_rel accept is sparse, so this cannot be promoted as calibrated reliability evidence without balancing/audit controls",
        },
        {
            "wave": "W2_connected_diagnostic",
            "route_role": "diagnostic_observability_then_topology",
            "predicates": "connected to",
            "planned_rows": diagnostic_rows,
            "source_rows": "existing ready connected-to packets",
            "target_axes": "diagnostic p_obs/topology uncertainty only",
            "p_obs_available": "all connected rows currently diagnostic/abstain because functional connection is ambiguous",
            "p_rel_available": "blocked",
            "use_now": "diagnostic taxonomy and failure analysis only",
            "caveat": "explicit topology/functional evidence rows are 0 in source inventory",
        },
        {
            "wave": "W3_full_train_expansion_deferred",
            "route_role": "future_capacity",
            "predicates": "attached to; hanging on; connected to",
            "planned_rows": 0,
            "source_rows": "556,038 full-train R7 rows as capacity pool",
            "target_axes": "future hard-negative mining and no-view/low-evidence p_obs controls",
            "p_obs_available": "not materialized in this wave",
            "p_rel_available": "not materialized in this wave",
            "use_now": "deferred",
            "caveat": "full-train candidates are unsupported by old verifier and need per-row packet/mesh/multiview materialization before targets",
        },
    ]


def feature_blocks() -> list[dict[str, Any]]:
    return [
        {
            "block": "T_e",
            "factor": "semantic_content",
            "materialize_next": True,
            "model_safe_fields": "predicate_label; predicate_family; subject_label; object_label; subject_family; object_family",
            "allowed_use": "compatibility input and semantic-only baseline",
            "forbidden": "source score; rank; query id; packet id; GT status; review labels",
            "notes": "Object labels remain semantic content, but class-pair-only probes must be run in schema audit.",
        },
        {
            "block": "G_e_attachment",
            "factor": "predicate_independent_geometry_evidence",
            "materialize_next": True,
            "model_safe_fields": "pair distance/gap; OBB overlap; point/mesh contact proxy; anchor surface proxy; relative pose; vertical offset; floor/support confound proxy; normal/orientation proxy when available",
            "allowed_use": "geometry-only baseline, T_e x G_e compatibility, shuffled-G controls",
            "forbidden": "predicate label; source score/rank; review labels; query/proxy construction fields; old p_geom_valid",
            "notes": "Recompute from scan/packet/mesh sources where possible; do not copy construction proxy fields as G_e.",
        },
        {
            "block": "Q_e_observability",
            "factor": "evidence_quality_observability",
            "materialize_next": True,
            "model_safe_fields": "mesh_packet_ready; multiview_packet_ready; contact_sheet_ready; subject/object image counts; same-frame co-visible flag; same-view weak flag; scan mesh/point/multiview availability; visual evidence tier",
            "allowed_use": "p_obs/selective decision and Q-only ablation",
            "forbidden": "review_coverage; review_endpoint_identity; review_uncertainty; p_obs target; packet id",
            "notes": "Q_e may encode evidence availability, not reviewer decisions.",
        },
        {
            "block": "Z_e",
            "factor": "source_confidence",
            "materialize_next": "hidden_diagnostic_only",
            "model_safe_fields": "none",
            "allowed_use": "hidden audit and source-only leakage probe",
            "forbidden": "all Z_e fields in C_e and p_obs materialization",
            "notes": "source score/rank can be exported only in hidden_manifest.",
        },
        {
            "block": "targets",
            "factor": "hidden_supervision",
            "materialize_next": True,
            "model_safe_fields": "none",
            "allowed_use": "target_manifest only",
            "forbidden": "targets inside model_safe_view",
            "notes": "p_rel is defined only for observable attached/hanging rows; connected-to p_rel remains blocked.",
        },
    ]


def output_contract() -> list[dict[str, Any]]:
    return [
        {
            "artifact": "source_rows.jsonl",
            "role": "all materialized rows with non-label source fields split into factor blocks",
            "contains_model_inputs": True,
            "contains_targets": False,
            "contains_hidden_fields": False,
        },
        {
            "artifact": "model_safe_view.jsonl",
            "role": "strict feature whitelist for schema audit and later smoke",
            "contains_model_inputs": True,
            "contains_targets": False,
            "contains_hidden_fields": False,
        },
        {
            "artifact": "target_manifest.jsonl",
            "role": "p_obs, p_rel_observable, multiclass diagnostic targets after label lock",
            "contains_model_inputs": False,
            "contains_targets": True,
            "contains_hidden_fields": False,
        },
        {
            "artifact": "hidden_manifest.jsonl",
            "role": "candidate ids, scan ids, instance ids, source rank/score, query/proxy/GT/construction fields for audit only",
            "contains_model_inputs": False,
            "contains_targets": False,
            "contains_hidden_fields": True,
        },
        {
            "artifact": "control_manifest.jsonl",
            "role": "wrong-T, shuffled-G, shuffled-Q, no-view, mesh-only, connected-diagnostic, and leakage probes",
            "contains_model_inputs": False,
            "contains_targets": False,
            "contains_hidden_fields": True,
        },
        {
            "artifact": "schema_audit_inputs.json",
            "role": "feature whitelist, blocked field list, group keys, and required probes for the next schema audit",
            "contains_model_inputs": False,
            "contains_targets": False,
            "contains_hidden_fields": False,
        },
    ]


def target_contract() -> list[dict[str, Any]]:
    return [
        {
            "target": "p_obs",
            "scope": "attached to; hanging on; connected diagnostic rows",
            "positive_definition": "evidence is sufficient to decide the relation",
            "negative_definition": "visual/mesh evidence is ambiguous, endpoint identity is uncertain, or relation is topology/functional uncertain",
            "materialize_next": True,
            "model_input_allowed": False,
            "gate_before_smoke": "p_obs must not be solvable by query id, packet id, source rank, or review labels",
        },
        {
            "target": "p_rel_observable",
            "scope": "attached to; hanging on only, p_obs-positive rows only",
            "positive_definition": "observable accept/reliable attachment or hanging relation",
            "negative_definition": "observable reject/unreliable relation",
            "materialize_next": True,
            "model_input_allowed": False,
            "gate_before_smoke": "positive sparsity and class-pair/query shortcuts must be audited before any learned claim",
        },
        {
            "target": "C_e_attachment",
            "scope": "attached to; hanging on after schema audit",
            "positive_definition": "T_e is compatible with predicate-independent G_e under observable evidence",
            "negative_definition": "same route but incompatible G_e or wrong predicate/geometry pairing",
            "materialize_next": "metadata_only_until_schema_audit",
            "model_input_allowed": False,
            "gate_before_smoke": "wrong-T and shuffled-G controls must be materialized",
        },
        {
            "target": "connected_to_diagnostic",
            "scope": "connected to",
            "positive_definition": "not defined in this wave",
            "negative_definition": "not defined in this wave",
            "materialize_next": "diagnostic_only",
            "model_input_allowed": False,
            "gate_before_smoke": "explicit topology or functional-connection source is required before p_rel",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    names = [
        "candidate_id",
        "packet_request_id",
        "packet_id",
        "query_id",
        "query_id_hidden",
        "selection_proxy_role_hidden",
        "selection_route_hidden",
        "cell_id_hidden",
        "rank_band_hidden",
        "semantic_rank_hidden",
        "semantic_score_norm_hidden",
        "source_score",
        "source_rank",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "object_id",
        "directed_pair_id",
        "visible_pair_key_hidden",
        "label_match_status_hidden",
        "matched_predicates_hidden",
        "gt_match_status",
        "p_geom_valid",
        "review_relation_reliability",
        "review_geometry_support",
        "review_coverage",
        "review_endpoint_identity",
        "review_uncertainty",
        "review_notes",
        "p_obs_target",
        "p_rel_target",
        "primary_relation_binary_target",
        "geometry_support_binary_target",
        "compatibility_binary_target",
    ]
    return [
        {
            "field": name,
            "model_safe_view_allowed": False,
            "allowed_location": "hidden_manifest or target_manifest only",
            "reason": "leakage, label, source-confidence, construction, identity, or audit provenance",
        }
        for name in names
    ]


def control_plan() -> list[dict[str, Any]]:
    return [
        {
            "control": "wrong_T_predicate",
            "purpose": "check whether G_e is interpreted through the correct predicate",
            "construction": "swap attached-to and hanging-on T_e while keeping G_e/Q_e fixed",
            "required_before_smoke": True,
        },
        {
            "control": "shuffled_G_same_predicate",
            "purpose": "check geometry-specific signal",
            "construction": "shuffle G_e within predicate and broad evidence tier",
            "required_before_smoke": True,
        },
        {
            "control": "shuffled_Q_same_predicate",
            "purpose": "check observability shortcut dependence",
            "construction": "shuffle Q_e within predicate and p_obs target band",
            "required_before_smoke": True,
        },
        {
            "control": "no_view_or_low_evidence_mask",
            "purpose": "test p_obs abstention behavior",
            "construction": "mask visual/multiview fields or use rows without strong pair visual evidence",
            "required_before_smoke": True,
        },
        {
            "control": "class_pair_only_probe",
            "purpose": "detect semantic class-pair shortcut",
            "construction": "train/evaluate simple class-pair and predicate-only probes during schema audit",
            "required_before_smoke": True,
        },
        {
            "control": "hidden_query_rank_source_probe",
            "purpose": "verify blocked construction/source fields would be risky if leaked",
            "construction": "audit-only probe using query id, rank, source score, packet id",
            "required_before_smoke": True,
        },
        {
            "control": "connected_to_diagnostic_probe",
            "purpose": "show connected-to lacks topology evidence for primary p_rel",
            "construction": "keep connected-to rows out of primary p_rel and report diagnostic confusion only",
            "required_before_smoke": True,
        },
    ]


def gate_plan() -> list[dict[str, Any]]:
    return [
        {
            "gate": "G0_plan_only",
            "requirement": "write plan artifacts only",
            "pass_condition": "no row materialization and no learned smoke in this step",
        },
        {
            "gate": "G1_factor_separation",
            "requirement": "materialization separates T_e, G_e, Q_e, hidden Z_e, and targets",
            "pass_condition": "model_safe_view has no hidden/source/review/target fields",
        },
        {
            "gate": "G2_p_obs_first",
            "requirement": "p_obs is defined for observability before p_rel",
            "pass_condition": "p_rel_observable exists only for p_obs-positive attached/hanging rows",
        },
        {
            "gate": "G3_connected_boundary",
            "requirement": "connected-to stays diagnostic",
            "pass_condition": "no connected-to p_rel target until explicit topology evidence exists",
        },
        {
            "gate": "G4_shortcut_audit_before_smoke",
            "requirement": "schema shortcut audit runs before any learned smoke",
            "pass_condition": "class-pair/query/rank/packet/review leakage probes are reported",
        },
        {
            "gate": "G5_p_rel_sparsity_warning",
            "requirement": "p_rel accept is sparse",
            "pass_condition": "no calibrated reliability claim unless balancing or robust evaluation is added",
        },
    ]


def materialization_steps() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "M1_join_source_inventory",
            "description": "join packet reuse inventory rows with locked ingested target rows by candidate_id",
            "writes_rows": True,
            "writes_model_features": False,
        },
        {
            "step_id": "M2_recompute_or_extract_G_e",
            "description": "recompute predicate-independent point/mesh/contact/pose evidence where possible; do not copy proxy labels as G_e",
            "writes_rows": True,
            "writes_model_features": True,
        },
        {
            "step_id": "M3_materialize_Q_e",
            "description": "write observability availability fields from packet/scan evidence, excluding review decisions",
            "writes_rows": True,
            "writes_model_features": True,
        },
        {
            "step_id": "M4_write_targets_hidden",
            "description": "write p_obs, p_rel_observable, multiclass diagnostic targets to target_manifest only",
            "writes_rows": True,
            "writes_model_features": False,
        },
        {
            "step_id": "M5_write_controls",
            "description": "write control manifest for wrong-T, shuffled-G, shuffled-Q, no-view, and hidden leakage probes",
            "writes_rows": True,
            "writes_model_features": False,
        },
        {
            "step_id": "M6_stop_before_smoke",
            "description": "stop at materialized rows; next stage is schema/shortcut audit, not learned smoke",
            "writes_rows": False,
            "writes_model_features": False,
        },
    ]


def report_text(summary: dict[str, Any], rows: dict[str, list[dict[str, Any]]]) -> str:
    quota = rows["row_quota_plan"]
    snap = summary["target_distribution_snapshot"]
    lines = [
        "# Attachment Observability Materialization Plan",
        "",
        f"Created: `{summary['created_at_utc']}`",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Planned Materialization",
        "",
        "| Wave | Predicates | Planned Rows | Use | Caveat |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in quota:
        lines.append(
            f"| `{row['wave']}` | {row['predicates']} | {row['planned_rows']} | {row['use_now']} | {row['caveat']} |"
        )
    lines.extend(
        [
            "",
            "## Target Snapshot",
            "",
            "```text",
            f"predicate_label = {snap.get('predicate_label')}",
            f"p_obs_target = {snap.get('p_obs_target')}",
            f"primary_binary_target = {snap.get('primary_binary_target')}",
            f"review_relation_reliability = {snap.get('review_relation_reliability')}",
            f"quick_probe_risk_flags = {snap.get('quick_probe_risk_flags')}",
            "```",
            "",
            "## Decision",
            "",
            "`attached to` and `hanging on` should be materialized as the primary R7 observability route. "
            "`connected to` remains diagnostic because source inventory found zero explicit topology/functional evidence rows.",
            "",
            "This plan intentionally stops before learned smoke. The next materialization must emit source rows, "
            "model-safe features, hidden targets, hidden provenance, and control manifests separately. Then a schema "
            "shortcut audit must run before any learned result is interpreted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    source_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    packet_summary = read_json(args.packet_dir / "summary.json")
    errors = validate_inputs(source_summary, source_errors, ingestion_summary, packet_summary)

    row_sets = {
        "row_quota_plan": row_quota_plan(source_summary, ingestion_summary),
        "feature_blocks": feature_blocks(),
        "output_contract": output_contract(),
        "target_contract": target_contract(),
        "blocked_fields": blocked_fields(),
        "control_plan": control_plan(),
        "gate_plan": gate_plan(),
        "materialization_steps": materialization_steps(),
    }
    status = STATUS_ERROR if errors else STATUS_READY
    selected_path = "input_errors_block_materialization_plan" if errors else SELECTED_PATH
    next_todo = "fix_attachment_observability_materialization_plan_inputs" if errors else NEXT_TODO

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "report": output_dir / "report.md",
        "row_quota_plan": output_dir / "row_quota_plan.csv",
        "feature_blocks": output_dir / "feature_blocks.csv",
        "output_contract": output_dir / "output_contract.csv",
        "target_contract": output_dir / "target_contract.csv",
        "blocked_fields": output_dir / "blocked_fields.csv",
        "control_plan": output_dir / "control_plan.csv",
        "gate_plan": output_dir / "gate_plan.csv",
        "materialization_steps": output_dir / "materialization_steps.csv",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "next_todo": next_todo,
        "input_paths": {
            "source_inventory": rel_path(args.source_inventory_dir / "summary.json"),
            "label_ingestion": rel_path(args.ingestion_dir / "summary.json"),
            "packet_materialization": rel_path(args.packet_dir / "summary.json"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "route": {
            "route_id": "R7",
            "family": "attachment_observability",
            "primary_predicates": list(PRIMARY_PREDICATES),
            "diagnostic_predicates": list(DIAGNOSTIC_PREDICATES),
        },
        "planned_rows": {
            "primary_attached_hanging": sum(
                int(row.get("planned_rows") or 0)
                for row in row_sets["row_quota_plan"]
                if row["wave"] == "W1_primary_attachment_observability"
            ),
            "connected_diagnostic": sum(
                int(row.get("planned_rows") or 0)
                for row in row_sets["row_quota_plan"]
                if row["wave"] == "W2_connected_diagnostic"
            ),
            "total_next_wave": 560,
        },
        "target_distribution_snapshot": distribution_snapshot(ingestion_summary),
        "source_inventory_snapshot": {
            "status": source_summary.get("status"),
            "full_train_rows_by_predicate": source_summary.get("full_train_inventory", {}).get("rows_by_predicate"),
            "packet_rows_by_predicate": source_summary.get("packet_reuse_inventory", {}).get("rows_by_predicate"),
            "route_readiness": source_summary.get("route_readiness"),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "runs_model": False,
            "trains_new_model": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "writes_plan_only": True,
            "next_materialization_may_write_rows": True,
        },
    }

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], errors)
    for key, rows in row_sets.items():
        write_csv(output_paths[key], rows)
    output_paths["report"].write_text(report_text(summary, row_sets), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
