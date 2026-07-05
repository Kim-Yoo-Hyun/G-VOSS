#!/usr/bin/env python3
"""Lock support/contact hard-route schema and shortcut audit review artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization"
)

EXPECTED_RUNTIME_STATUS = "h002_support_contact_harder_schema_shortcut_audit_ready_with_warnings"
EXPECTED_RUNTIME_SCHEMA = "h002_support_contact_harder_schema_shortcut_audit_v1"

SCHEMA_VERSION = "h002_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization_v1"
STATUS_READY = "h002_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization_ready_with_warnings"
STATUS_ERRORS = "h002_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization_errors"
SELECTED_PATH = "support_contact_harder_route_schema_ready_select_metric_protocol_freeze"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


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


def validate_audit(audit_dir: Path, manifest: dict[str, Any], runtime_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if manifest.get("schema_version") != EXPECTED_RUNTIME_SCHEMA:
        errors.append({"error_type": "unexpected_runtime_schema", "actual": manifest.get("schema_version")})
    if manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0 or runtime_errors:
        errors.append(
            {
                "error_type": "runtime_validation_errors_present",
                "summary_errors": manifest.get("validation_errors"),
                "file_errors": len(runtime_errors),
            }
        )
    decision = manifest.get("decision", {})
    if decision.get("schema_audit_passed") is not True:
        errors.append({"error_type": "schema_audit_not_passed", "actual": decision.get("schema_audit_passed")})
    if decision.get("metric_protocol_freeze_next") is not True:
        errors.append({"error_type": "metric_protocol_freeze_not_allowed", "actual": decision.get("metric_protocol_freeze_next")})
    if decision.get("paper_metric_promoted") is not False:
        errors.append({"error_type": "paper_metric_promoted_too_early", "actual": decision.get("paper_metric_promoted")})
    if decision.get("support_contact_solved_claim_allowed") is not False:
        errors.append(
            {
                "error_type": "support_contact_solved_claim_allowed_too_early",
                "actual": decision.get("support_contact_solved_claim_allowed"),
            }
        )
    boundary = manifest.get("boundary", {})
    for key in ["metrics_run", "official_test_usage", "paper_metric_produced"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_boundary_true", "key": key, "actual": boundary.get(key)})
    if boundary.get("primary_view") != "model_safe_main_no_class":
        errors.append({"error_type": "unexpected_primary_view", "actual": boundary.get("primary_view")})

    for filename in [
        "file_counts.csv",
        "view_alignment.csv",
        "main_view_summary.csv",
        "feature_availability.csv",
        "blocked_field_hits.jsonl",
        "group_integrity.csv",
        "shortcut_risk_table.csv",
        "shortcut_warnings.csv",
        "control_readiness.csv",
        "next_contract.json",
        "report.md",
    ]:
        if not (audit_dir / filename).exists():
            errors.append({"error_type": "missing_runtime_artifact", "file": filename})
    return errors


def build_report(summary: dict[str, Any], shortcut_warnings: list[dict[str, Any]], controls: list[dict[str, Any]]) -> str:
    shortcut_lines = "\n".join(
        f"- `{row.get('probe')}`: majority={row.get('majority_accuracy')}, risk={row.get('risk')}, "
        f"blocks_solved_claim={row.get('blocks_solved_claim')}"
        for row in shortcut_warnings
    )
    control_lines = "\n".join(
        f"- `{row.get('control')}`: ready={row.get('ready')}, blocks_metric_freeze={row.get('blocks_metric_freeze')}"
        for row in controls
    )
    return f"""# Support/Contact Harder Route Schema Shortcut Audit Review

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
shortcut_warnings = {summary['shortcut_warnings']}
high_shortcut_warnings = {summary['high_shortcut_warnings']}
next_todo = {summary['next_todo']}
```

이 artifact는 Docker runtime schema/shortcut audit를 hypothesis 기록으로 고정한다.
Metric은 실행하지 않았고 official test도 사용하지 않았다.

## Key Result

- primary view: `model_safe_main_no_class`
- rows: `{summary['main_view']['rows']}`
- feature_count: `{summary['main_view']['feature_count']}`
- labels: `{summary['main_view']['label_0']}` reject / `{summary['main_view']['label_1']}` accept
- predicate balance: `{summary['main_view']['standing_on']}` `standing on`, `{summary['main_view']['lying_on']}` `lying on`
- blocked field hits: `{summary['main_view']['blocked_field_hits']}`
- bad groups: `{summary['group_summary']['bad_group_count']}`

## Shortcut Warnings

{shortcut_lines or "- none"}

`predicate x class-pair` shortcut은 high-risk이므로 다음 metric protocol에서
class-controlled split/control과 shortcut baseline 비교를 필수로 둔다.
이 warning은 metric freeze 자체를 막지는 않지만, `support_contact solved` claim은 막는다.

## Control Readiness

{control_lines or "- none"}

## Boundary

- no paper metric
- no official test
- no source reranking
- no `p_obs` / `p_rel` claim
- `Q_e`는 diagnostic-only
- class labels는 ablation-only
"""


def main() -> int:
    args = parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    manifest_path = args.audit_dir / "audit_manifest.json"
    manifest = read_json(manifest_path)
    runtime_errors = read_jsonl(args.audit_dir / "validation_errors.jsonl")
    validation_errors = validate_audit(args.audit_dir, manifest, runtime_errors)

    shortcut_warnings = read_csv(args.audit_dir / "shortcut_warnings.csv")
    controls = read_csv(args.audit_dir / "control_readiness.csv")
    shortcut_table = read_csv(args.audit_dir / "shortcut_risk_table.csv")

    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "selected_path": SELECTED_PATH if not validation_errors else "blocked",
        "next_todo": NEXT_TODO if not validation_errors else None,
        "validation_errors": len(validation_errors),
        "runtime_audit_dir": rel_path(args.audit_dir),
        "runtime_status": manifest.get("status"),
        "runtime_validation_errors": manifest.get("validation_errors"),
        "main_view": manifest.get("main_view", {}),
        "group_summary": manifest.get("group_summary", {}),
        "shortcut_warnings": len(shortcut_warnings),
        "high_shortcut_warnings": sum(1 for row in shortcut_warnings if row.get("risk") == "high"),
        "control_ready_count": sum(1 for row in controls if row.get("ready") == "True"),
        "control_count": len(controls),
        "decision": {
            "schema_audit_passed": not bool(validation_errors),
            "metric_protocol_freeze_next": not bool(validation_errors),
            "paper_metric_promoted": False,
            "support_contact_solved_claim_allowed": False,
            "shortcut_warnings_require_controls": bool(shortcut_warnings),
        },
        "claim_boundary": {
            "support_contact_role": "hard_compatibility_route_candidate",
            "support_contact_solved_claim": False,
            "q_e_role": "diagnostic_only",
            "class_label_role": "ablation_only",
            "official_test_usage": False,
            "metrics_run": False,
        },
        "output_artifacts": {
            "summary": rel_path(out / "summary.json"),
            "validation_errors": rel_path(out / "validation_errors.jsonl"),
            "shortcut_warnings": rel_path(out / "shortcut_warnings.csv"),
            "shortcut_risk_table": rel_path(out / "shortcut_risk_table.csv"),
            "control_readiness": rel_path(out / "control_readiness.csv"),
            "next_contract": rel_path(out / "next_contract.json"),
            "report": rel_path(out / "report.md"),
        },
    }

    next_contract = {
        "next_todo": NEXT_TODO if not validation_errors else None,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked",
        "purpose": "Freeze support/contact hard-route metric protocol after schema audit passes with shortcut warnings.",
        "must_include": [
            "semantic-only, geometry-only, concat, interaction, class-ablation baselines",
            "wrong-T same-route control",
            "shuffled-G global and within-class-pair controls",
            "predicate-only and predicate x class-pair shortcut baselines",
            "family wording: challenging compatibility route, not solved relation family",
        ],
        "must_not_do": [
            "do not use official test",
            "do not promote support_contact as solved",
            "do not put Q_e into primary C_e metric input",
            "do not put class labels into primary no-class view",
        ],
    }

    write_json(out / "summary.json", summary)
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    write_csv(out / "shortcut_warnings.csv", shortcut_warnings)
    write_csv(out / "shortcut_risk_table.csv", shortcut_table)
    write_csv(out / "control_readiness.csv", controls)
    write_json(out / "next_contract.json", next_contract)
    (out / "report.md").write_text(build_report(summary, shortcut_warnings, controls), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
