#!/usr/bin/env python3
"""Ingest class-pair repair labels after visible-packet label lock."""

from __future__ import annotations

from typing import Any
from pathlib import Path

import compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion as base


H2_ROOT = Path(__file__).resolve().parents[1]

base.DEFAULT_FILL_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill"
)
base.DEFAULT_PACKET_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization"
)
base.DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion"
)

base.EXPECTED_FILL_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_completed"
)
base.EXPECTED_FILL_NEXT = (
    "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion"
)
base.EXPECTED_PACKET_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_ready_for_label_fill"
)

base.SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion_v1"
)
base.TARGET_SCHEMA_VERSION = "h002_support_contact_visual_mesh_audit_class_pair_repair_targets_v1"
base.STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested_ready_for_controlled_smoke_plan"
)
base.STATUS_SHORTCUT_RISK = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested_shortcut_risk_blocks_smoke"
)
base.STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion_errors"
)
base.SELECTED_PATH = "ingest_class_pair_repair_labels_run_shortcut_diagnostics"
base.NEXT_TODO = (
    "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion"
)

GENERIC = {"object", "objects", "item", "items", "thing", "things", "stuff", "clutter"}


def generic_endpoint_role(subject: Any, obj: Any) -> str:
    subject_generic = base.norm(subject) in GENERIC
    object_generic = base.norm(obj) in GENERIC
    if subject_generic and object_generic:
        return "both_generic"
    if subject_generic:
        return "subject_generic"
    if object_generic:
        return "object_generic"
    return "none"


_base_derive_targets = base.derive_targets
_base_target_count_rows = base.target_count_rows
_base_risk_register_rows = base.risk_register_rows
_base_write_json = base.write_json


def derive_targets(filled: dict[str, Any], hidden: dict[str, Any]) -> dict[str, Any]:
    row = _base_derive_targets(filled, hidden)
    role = generic_endpoint_role(filled.get("subject_label"), filled.get("object_label"))
    row.update(
        {
            "predicate_x_subject_object_class_pair_visible": (
                f"{filled.get('predicate_label')}::{filled.get('subject_label')}->{filled.get('object_label')}"
            ),
            "generic_endpoint_visible": str(role != "none"),
            "generic_endpoint_role_visible": role,
            "repair_proxy_kind_hidden": hidden.get("repair_proxy_kind"),
            "predicate_class_pair_hidden": hidden.get("predicate_class_pair"),
        }
    )
    return row


def target_count_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = _base_target_count_rows(rows)
    for field in [
        "generic_endpoint_visible",
        "generic_endpoint_role_visible",
        "repair_proxy_kind_hidden",
        "predicate_class_pair_hidden",
        "predicate_x_subject_object_class_pair_visible",
    ]:
        counts = base.Counter(str(row.get(field)) for row in rows)
        total = sum(counts.values()) or 1
        for value, count in counts.most_common():
            out.append({"axis": field, "value": value, "count": count, "share": count / total})
    return out


def risk_register_rows(viability: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = _base_risk_register_rows(viability)
    rows.append(
        {
            "risk": "generic_endpoint_shortcut",
            "severity": "high",
            "evidence": "generic endpoints were a major abstain source in class-pair repair labels",
            "action": "audit generic_endpoint_visible and generic_endpoint_role_visible before any learned smoke",
        }
    )
    rows.append(
        {
            "risk": "repair_proxy_kind_leakage",
            "severity": "high",
            "evidence": "repair_proxy_kind was used for sampling and must remain hidden from model inputs",
            "action": "use repair_proxy_kind only for post-lock audit and balancing diagnostics",
        }
    )
    return rows


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Label Ingestion",
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
            "## Target Summary",
            "",
            "```json",
            base.json.dumps(summary["target_summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            "The class-pair repair target has enough binary row mass, but learned smoke remains blocked until the post-lock shortcut diagnostics are reviewed. Generic endpoint and hidden repair-proxy risks are tracked explicitly in this ingestion.",
            "",
        ]
    )


def write_json(path: Path, payload: Any) -> None:
    if path.name == "model_input_boundary.json" and isinstance(payload, dict):
        blocked = payload.setdefault("blocked_model_inputs", [])
        for field in [
            "repair_proxy_kind_hidden",
            "predicate_class_pair_hidden",
            "generic_endpoint_visible unless used only as a stratification/control variable",
            "generic_endpoint_role_visible unless used only as a stratification/control variable",
            "predicate_x_subject_object_class_pair_visible as a direct shortcut feature",
        ]:
            if field not in blocked:
                blocked.append(field)
        payload["reason"] = (
            payload.get("reason", "")
            + "; class-pair repair ingestion found residual predicate-class and generic-endpoint shortcuts"
        ).strip("; ")
    _base_write_json(path, payload)


base.derive_targets = derive_targets
base.target_count_rows = target_count_rows
base.risk_register_rows = risk_register_rows
base.build_report = build_report
base.write_json = write_json

base.PREDICTOR_CATEGORIES["visible_semantic"].update(
    {
        "predicate_x_subject_object_class_pair_visible",
        "generic_endpoint_visible",
        "generic_endpoint_role_visible",
    }
)
base.PREDICTOR_CATEGORIES["construction_or_source_hidden"].update(
    {
        "repair_proxy_kind_hidden",
        "predicate_class_pair_hidden",
    }
)
base.RISK_PREDICTORS = sorted({field for fields in base.PREDICTOR_CATEGORIES.values() for field in fields})


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
