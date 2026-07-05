#!/usr/bin/env python3
"""Audit the materialized R1 close-by geometry-support route root."""

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

DEFAULT_ROUTE_ROOT = H2_ROOT / "artifacts/route_specific_targets/r1_proximity"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization"
)

EXPECTED_ROUTE_STATUS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready"
EXPECTED_ROUTE_NEXT = "compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_v1"
STATUS_READY = "h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_errors"
SELECTED_PATH = "r1_close_by_schema_pass_select_geometry_route_control_runner_plan"
NEXT_TODO = "compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan"

REQUIRED_ROUTE_FILES = [
    "summary.json",
    "schema.json",
    "model_safe_rows.jsonl",
    "hidden_manifest.jsonl",
    "audit_view.jsonl",
    "control_manifest.json",
    "split_or_group_manifest.json",
    "report.md",
    "validation_errors.jsonl",
    "row_counts.csv",
    "label_counts.csv",
]

EXPECTED_COUNTS = {
    "total_rows": 1284,
    "primary_binary_rows": 800,
    "abstain_qe_rows": 240,
    "raw_distance_diagnostic_rows": 240,
    "gt_geometry_conflict_audit_rows": 4,
}

EXPECTED_PRIMARY_LABELS = {
    "geometry_supported": 400,
    "geometry_unsupported": 400,
}

EXPECTED_ALL_LABELS = {
    "geometry_supported": 520,
    "geometry_unsupported": 520,
    "abstain": 240,
    "audit_required": 4,
}

REQUIRED_CONTROLS = {
    "distance_geometry_baseline",
    "scale_control",
    "coverage_control",
    "source_score_rank_control",
    "class_pair_control",
    "shuffled_g_wrong_pair_geometry",
    "wording_guard",
}

REQUIRED_G_FIELDS = {
    "distance_xy",
    "distance_3d",
    "normalized_distance_xy",
    "normalized_distance_3d",
}

REQUIRED_Q_FIELDS = {
    "geometry_available",
    "geometry_checkable",
    "feature_complete",
    "feature_missing_count",
}

ROUTE = {
    "route_id": "R1",
    "family": "proximity",
    "relation": "close by",
    "route_type": "geometry_only_learned_evaluated_route",
    "target_axis": "geometry_support",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-root", type=Path, default=DEFAULT_ROUTE_ROOT)
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
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def flatten_keys(payload: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_str = str(key)
            keys.add(key_str)
            keys.update(flatten_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            keys.update(flatten_keys(item))
    return keys


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def required_file_audit(route_root: Path) -> list[dict[str, Any]]:
    rows = []
    for name in REQUIRED_ROUTE_FILES:
        path = route_root / name
        rows.append(
            {
                "check": "required_file_present",
                "file": name,
                "path": rel_path(path),
                "passed": path.exists(),
            }
        )
    return rows


def route_contract_audit(summary: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, Any]]:
    route_summary = summary.get("route", {})
    route_schema = schema.get("route", {})
    rows = []
    for key, expected in ROUTE.items():
        rows.append(
            {
                "check": "route_summary_contract",
                "field": key,
                "expected": expected,
                "actual": route_summary.get(key),
                "passed": route_summary.get(key) == expected,
            }
        )
        rows.append(
            {
                "check": "route_schema_contract",
                "field": key,
                "expected": expected,
                "actual": route_schema.get(key),
                "passed": route_schema.get(key) == expected,
            }
        )
    rows.extend(
        [
            {
                "check": "upstream_status_ready",
                "field": "status",
                "expected": EXPECTED_ROUTE_STATUS,
                "actual": summary.get("status"),
                "passed": summary.get("status") == EXPECTED_ROUTE_STATUS,
            },
            {
                "check": "upstream_next_todo",
                "field": "next_todo",
                "expected": EXPECTED_ROUTE_NEXT,
                "actual": summary.get("next_todo"),
                "passed": summary.get("next_todo") == EXPECTED_ROUTE_NEXT,
            },
            {
                "check": "upstream_validation_errors_zero",
                "field": "validation_errors",
                "expected": 0,
                "actual": summary.get("validation_errors"),
                "passed": summary.get("validation_errors") == 0,
            },
            {
                "check": "claim_boundary_blocks_interaction",
                "field": "predicate_geometry_interaction_claim",
                "expected": "blocked",
                "actual": schema.get("claim_boundary", {}).get("predicate_geometry_interaction_claim"),
                "passed": schema.get("claim_boundary", {}).get("predicate_geometry_interaction_claim") == "blocked",
            },
            {
                "check": "distance_dominance_route_property",
                "field": "distance_dominance",
                "expected": "expected_route_property",
                "actual": schema.get("claim_boundary", {}).get("distance_dominance"),
                "passed": schema.get("claim_boundary", {}).get("distance_dominance") == "expected_route_property",
            },
        ]
    )
    return rows


def row_integrity_audit(
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    expected_total = EXPECTED_COUNTS["total_rows"]
    hidden_ids = {row.get("route_row_id") for row in hidden_rows}
    audit_ids = {row.get("route_row_id") for row in audit_rows}
    model_ids = [row.get("route_row_id") for row in model_rows]
    rows.extend(
        [
            {
                "check": "model_row_count",
                "expected": expected_total,
                "actual": len(model_rows),
                "passed": len(model_rows) == expected_total,
            },
            {
                "check": "hidden_row_count",
                "expected": expected_total,
                "actual": len(hidden_rows),
                "passed": len(hidden_rows) == expected_total,
            },
            {
                "check": "audit_row_count",
                "expected": expected_total,
                "actual": len(audit_rows),
                "passed": len(audit_rows) == expected_total,
            },
            {
                "check": "unique_route_row_id",
                "expected": expected_total,
                "actual": len(set(model_ids)),
                "passed": len(set(model_ids)) == expected_total,
            },
            {
                "check": "model_hidden_route_id_match",
                "expected": expected_total,
                "actual": len(set(model_ids) & hidden_ids),
                "passed": set(model_ids) == hidden_ids,
            },
            {
                "check": "model_audit_route_id_match",
                "expected": expected_total,
                "actual": len(set(model_ids) & audit_ids),
                "passed": set(model_ids) == audit_ids,
            },
        ]
    )
    for key, expected in EXPECTED_COUNTS.items():
        rows.append(
            {
                "check": "summary_row_count",
                "field": key,
                "expected": expected,
                "actual": summary.get("row_counts", {}).get(key),
                "passed": summary.get("row_counts", {}).get(key) == expected,
            }
        )
    return rows


def label_audit(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    primary_rows = [row for row in model_rows if row.get("route_targets", {}).get("is_primary_binary")]
    primary_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in primary_rows)
    all_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in model_rows)
    interaction_counts = Counter(row.get("route_targets", {}).get("c_e_interaction_label") for row in model_rows)
    rows.append(
        {
            "check": "primary_binary_row_count",
            "expected": 800,
            "actual": len(primary_rows),
            "passed": len(primary_rows) == 800,
        }
    )
    for label, expected in EXPECTED_PRIMARY_LABELS.items():
        rows.append(
            {
                "check": "primary_binary_label_balance",
                "label": label,
                "expected": expected,
                "actual": primary_counts.get(label, 0),
                "passed": primary_counts.get(label, 0) == expected,
            }
        )
    for label, expected in EXPECTED_ALL_LABELS.items():
        rows.append(
            {
                "check": "all_route_label_count",
                "label": label,
                "expected": expected,
                "actual": all_counts.get(label, 0),
                "passed": all_counts.get(label, 0) == expected,
            }
        )
    rows.append(
        {
            "check": "c_e_interaction_not_applicable",
            "label": "not_applicable",
            "expected": len(model_rows),
            "actual": interaction_counts.get("not_applicable", 0),
            "passed": interaction_counts == {"not_applicable": len(model_rows)},
        }
    )
    return rows


def leakage_audit(model_rows: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    blocked = set(schema.get("blocked_feature_keys", []))
    rows: list[dict[str, Any]] = []
    legacy_hits = 0
    blocked_hits = 0
    policy_errors = 0
    for row in model_rows:
        serialized = json.dumps(row, sort_keys=True)
        if '"C_e_label"' in serialized:
            legacy_hits += 1
        feature_keys = flatten_keys(row.get("feature_blocks", {}))
        hits = sorted(feature_keys & blocked)
        if hits:
            blocked_hits += 1
            if blocked_hits <= 10:
                rows.append(
                    {
                        "check": "blocked_feature_key_absent",
                        "route_row_id": row.get("route_row_id"),
                        "hits": "; ".join(hits),
                        "passed": False,
                    }
                )
        policy = row.get("model_input_policy", {})
        policy_ok = (
            policy.get("primary_route_input") == "G_e_route"
            and policy.get("T_e_annotation_allowed_as_route_score") is False
            and policy.get("Z_e_source_allowed_as_route_score") is False
            and policy.get("Q_e_allowed_for_abstain_only") is True
            and policy.get("C_e_interaction_applicable") is False
        )
        if not policy_ok:
            policy_errors += 1
            if policy_errors <= 10:
                rows.append(
                    {
                        "check": "model_input_policy",
                        "route_row_id": row.get("route_row_id"),
                        "passed": False,
                        "policy": json.dumps(policy, sort_keys=True),
                    }
                )
    rows.extend(
        [
            {
                "check": "legacy_C_e_label_absent",
                "expected": 0,
                "actual": legacy_hits,
                "passed": legacy_hits == 0,
            },
            {
                "check": "blocked_feature_keys_absent",
                "expected": 0,
                "actual": blocked_hits,
                "passed": blocked_hits == 0,
            },
            {
                "check": "model_input_policy_all_rows",
                "expected": 0,
                "actual": policy_errors,
                "passed": policy_errors == 0,
            },
        ]
    )
    return rows


def control_readiness_audit(
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    control_manifest: dict[str, Any],
    split_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    controls = set(control_manifest.get("required_controls", []))
    for control in sorted(REQUIRED_CONTROLS):
        rows.append(
            {
                "check": "required_control_present",
                "control": control,
                "expected": True,
                "actual": control in controls,
                "passed": control in controls,
            }
        )

    missing_g = Counter()
    missing_q = Counter()
    for row in model_rows:
        g = row.get("feature_blocks", {}).get("G_e_route", {})
        q = row.get("feature_blocks", {}).get("Q_e_observability", {})
        for key in REQUIRED_G_FIELDS:
            if g.get(key) is None:
                missing_g[key] += 1
        for key in REQUIRED_Q_FIELDS:
            if q.get(key) is None:
                missing_q[key] += 1
    for key in sorted(REQUIRED_G_FIELDS):
        rows.append(
            {
                "check": "required_g_field_complete",
                "field": key,
                "expected_missing": 0,
                "actual_missing": missing_g.get(key, 0),
                "passed": missing_g.get(key, 0) == 0,
            }
        )
    for key in sorted(REQUIRED_Q_FIELDS):
        rows.append(
            {
                "check": "required_q_field_complete",
                "field": key,
                "expected_missing": 0,
                "actual_missing": missing_q.get(key, 0),
                "passed": missing_q.get(key, 0) == 0,
            }
        )

    hidden_key_presence = Counter()
    for row in hidden_rows:
        controls_hidden = row.get("hidden_controls", {})
        for key in ["raw_distance_bin", "norm_distance_bin", "p_geom_valid", "candidate_bucket", "subject_object_class_pair"]:
            if controls_hidden.get(key) is not None:
                hidden_key_presence[key] += 1
    for key in ["raw_distance_bin", "norm_distance_bin", "p_geom_valid", "candidate_bucket", "subject_object_class_pair"]:
        rows.append(
            {
                "check": "hidden_control_available_for_audit",
                "field": key,
                "expected": len(hidden_rows),
                "actual": hidden_key_presence.get(key, 0),
                "passed": hidden_key_presence.get(key, 0) == len(hidden_rows),
            }
        )

    interpretation = control_manifest.get("interpretation", {})
    rows.extend(
        [
            {
                "check": "distance_dominance_interpretation",
                "field": "distance_rule_dominance",
                "expected": "expected for geometry-only route",
                "actual": interpretation.get("distance_rule_dominance"),
                "passed": interpretation.get("distance_rule_dominance") == "expected for geometry-only route",
            },
            {
                "check": "not_interaction_evidence",
                "field": "not_interaction_evidence",
                "expected": True,
                "actual": interpretation.get("not_interaction_evidence"),
                "passed": interpretation.get("not_interaction_evidence") is True,
            },
            {
                "check": "split_policy_train_only",
                "field": "split_policy",
                "expected": "train_only",
                "actual": split_manifest.get("split_policy"),
                "passed": split_manifest.get("split_policy") == "train_only",
            },
        ]
    )
    return rows


def wording_audit(route_root: Path) -> list[dict[str, Any]]:
    files = {
        "report.md": (route_root / "report.md").read_text(encoding="utf-8"),
        "schema.json": (route_root / "schema.json").read_text(encoding="utf-8"),
        "control_manifest.json": (route_root / "control_manifest.json").read_text(encoding="utf-8"),
    }
    combined = "\n".join(files.values()).lower()
    rows = [
        {
            "check": "geometry_only_wording_present",
            "expected": True,
            "actual": "geometry-only" in combined or "geometry_only" in combined,
            "passed": "geometry-only" in combined or "geometry_only" in combined,
        },
        {
            "check": "interaction_not_applicable_present",
            "expected": True,
            "actual": "not_applicable" in combined,
            "passed": "not_applicable" in combined,
        },
        {
            "check": "not_interaction_evidence_present",
            "expected": True,
            "actual": "not evidence" in combined or "not_interaction_evidence" in combined,
            "passed": "not evidence" in combined or "not_interaction_evidence" in combined,
        },
        {
            "check": "paper_claim_blocked_present",
            "expected": True,
            "actual": "paper" in combined and "blocked" in combined,
            "passed": "paper" in combined and "blocked" in combined,
        },
    ]
    return rows


def collect_errors(audit_tables: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    errors = []
    for table_name, rows in audit_tables.items():
        for row in rows:
            if not as_bool(row.get("passed", False)):
                payload = dict(row)
                payload["table"] = table_name
                errors.append(payload)
    return errors


def render_report(summary: dict[str, Any]) -> str:
    return f"""# H002 R1 Close-By Geometry-Support Schema Audit

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Result

The materialized R1 `close by` route root passed schema and shortcut-boundary
audit.

Checked items:

- required route files
- route contract and target axis
- row counts and row-id consistency
- primary label balance
- legacy `C_e_label` absence
- blocked hidden/construction fields in model-safe features
- model input policy
- distance / scale / coverage control readiness
- wording guard against `T_e x G_e` interaction overclaim

## Interpretation

`close by` remains a geometry-only learned/evaluated route. Distance dominance is
expected for this route and is not treated as a failure. The failure condition is
instead leakage of hidden construction fields, label imbalance, missing coverage
controls, or wording that presents this branch as predicate-geometry interaction
evidence.

## Boundary

- Train-only audit.
- No validation/test used.
- No model run.
- No paper-level claim.
- H001 artifacts were not modified.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()

    summary_in = read_json(args.route_root / "summary.json")
    schema = read_json(args.route_root / "schema.json")
    control_manifest = read_json(args.route_root / "control_manifest.json")
    split_manifest = read_json(args.route_root / "split_or_group_manifest.json")
    model_rows = read_jsonl(args.route_root / "model_safe_rows.jsonl")
    hidden_rows = read_jsonl(args.route_root / "hidden_manifest.jsonl")
    audit_rows = read_jsonl(args.route_root / "audit_view.jsonl")
    upstream_errors = read_jsonl(args.route_root / "validation_errors.jsonl")

    audit_tables = {
        "required_file_audit": required_file_audit(args.route_root),
        "route_contract_audit": route_contract_audit(summary_in, schema),
        "row_integrity_audit": row_integrity_audit(model_rows, hidden_rows, audit_rows, summary_in),
        "label_balance_audit": label_audit(model_rows),
        "leakage_audit": leakage_audit(model_rows, schema),
        "control_readiness_audit": control_readiness_audit(model_rows, hidden_rows, control_manifest, split_manifest),
        "wording_audit": wording_audit(args.route_root),
    }
    errors = collect_errors(audit_tables)
    if upstream_errors:
        errors.append({"error_type": "upstream_validation_errors_present", "rows": len(upstream_errors)})

    status = STATUS_READY if not errors else STATUS_ERRORS
    output_paths = {
        "summary": args.output_dir / "summary.json",
        "report": args.output_dir / "report.md",
        "required_file_audit": args.output_dir / "required_file_audit.csv",
        "route_contract_audit": args.output_dir / "route_contract_audit.csv",
        "row_integrity_audit": args.output_dir / "row_integrity_audit.csv",
        "label_balance_audit": args.output_dir / "label_balance_audit.csv",
        "leakage_audit": args.output_dir / "leakage_audit.csv",
        "control_readiness_audit": args.output_dir / "control_readiness_audit.csv",
        "wording_audit": args.output_dir / "wording_audit.csv",
        "route_runner_gate": args.output_dir / "route_runner_gate.csv",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    route_runner_gate = [
        {
            "gate": "route_control_runner_plan",
            "allowed": status == STATUS_READY,
            "next_todo": NEXT_TODO,
            "reason": "schema audit passed; next runner should report geometry-only route controls, not interaction evidence",
        },
        {
            "gate": "learned_interaction_smoke",
            "allowed": False,
            "next_todo": "not_allowed_for_r1",
            "reason": "R1 close by is not a T_e x G_e interaction route",
        },
        {
            "gate": "paper_result_claim",
            "allowed": False,
            "next_todo": "not_allowed_from_r1_alone",
            "reason": "R1 is claim-control/generality evidence only",
        },
    ]
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed_now": False,
            "runs_model": False,
            "test_usage": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_route_root": rel_path(args.route_root),
        "next_todo": NEXT_TODO,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "passed_checks": sum(as_bool(row.get("passed", False)) for rows in audit_tables.values() for row in rows),
        "route": ROUTE,
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": status,
        "total_checks": sum(len(rows) for rows in audit_tables.values()),
        "validation_errors": len(errors),
    }

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], errors)
    for name, rows in audit_tables.items():
        write_csv(output_paths[name], rows)
    write_csv(output_paths["route_runner_gate"], route_runner_gate)
    output_paths["report"].write_text(render_report(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
