#!/usr/bin/env python3
"""Fill labels for class-pair controlled support/contact repair packets."""

from __future__ import annotations

from pathlib import Path

import compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill as base


H2_ROOT = Path(__file__).resolve().parents[1]

base.DEFAULT_PACKET_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization"
)
base.DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill"
)

base.EXPECTED_PACKET_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization_ready_for_label_fill"
)
base.EXPECTED_PACKET_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill"

base.SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_v1"
base.STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_completed"
)
base.STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_fill_errors"
)
base.SELECTED_PATH = "codex_visible_packet_proxy_labels_filled_for_class_pair_repair_user_requested"
base.NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion"
base.LABEL_POLICY = "support_contact_class_pair_repair_visible_packet_proxy_v1"


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
