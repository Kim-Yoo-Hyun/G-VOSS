#!/usr/bin/env python3
"""Freeze the Open3DSG raw-dump identity audit before raw dump inspection."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_raw_dump_identity_audit_v1"
RAW_SCHEMA_VERSION = "h001_open3dsg_raw_dump_v1"
EXPECTED_SCANS = 127
EXPECTED_CONTEXTS = 388
EXPECTED_DIRECTED_PAIRS = 25916
STATUS_READY_MISSING = "raw_dump_identity_checklist_ready_raw_dump_missing"
STATUS_AUDIT_READY = "raw_dump_identity_audit_ready"
STATUS_AUDIT_BLOCKED = "raw_dump_identity_audit_blocked"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--raw-dump-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl"),
    )
    parser.add_argument(
        "--predictions-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl"),
    )
    parser.add_argument(
        "--subset-json",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity"),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_selected_scans(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def build_scope(repo_root: Path, subset_json: Path, selected_scans: Path) -> dict[str, Any]:
    blockers: list[str] = []
    if not subset_json.is_file():
        blockers.append(f"missing_subset_json:{relpath(repo_root, subset_json)}")
        return {"status": "blocked", "blockers": blockers}
    if not selected_scans.is_file():
        blockers.append(f"missing_selected_scans:{relpath(repo_root, selected_scans)}")
        return {"status": "blocked", "blockers": blockers}

    selected = read_selected_scans(selected_scans)
    subset = load_json(subset_json)
    contexts: dict[str, dict[str, Any]] = {}
    directed_pairs = 0
    object_count_hist = Counter()
    for entry in subset.get("scans", []):
        scan_id = str(entry.get("scan"))
        if scan_id not in selected:
            continue
        split_id = int(entry.get("split"))
        objects = {int(key): str(value) for key, value in entry.get("objects", {}).items()}
        subgraph_id = f"{scan_id}_{split_id}"
        object_count = len(objects)
        directed_pairs += object_count * (object_count - 1)
        object_count_hist[object_count] += 1
        contexts[subgraph_id] = {
            "scan_id": scan_id,
            "subset_split_id": split_id,
            "subgraph_id": subgraph_id,
            "object_ids": sorted(objects),
            "object_count": object_count,
        }

    if len(selected) != EXPECTED_SCANS:
        blockers.append(f"selected_scans:{len(selected)}/{EXPECTED_SCANS}")
    if len(contexts) != EXPECTED_CONTEXTS:
        blockers.append(f"contexts:{len(contexts)}/{EXPECTED_CONTEXTS}")
    if directed_pairs != EXPECTED_DIRECTED_PAIRS:
        blockers.append(f"directed_pairs:{directed_pairs}/{EXPECTED_DIRECTED_PAIRS}")

    return {
        "status": "ready" if not blockers else "blocked",
        "selected_scans_path": relpath(repo_root, selected_scans),
        "subset_json": relpath(repo_root, subset_json),
        "selected_scans": len(selected),
        "contexts": len(contexts),
        "directed_pairs": directed_pairs,
        "object_count_histogram": {str(key): value for key, value in sorted(object_count_hist.items())},
        "context_sample": list(contexts.values())[:5],
        "context_ids": sorted(contexts),
        "blockers": blockers,
    }


def checklist() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_schema_version": RAW_SCHEMA_VERSION,
        "required_raw_fields": [
            "schema_version",
            "record_type",
            "baseline_run_id",
            "scan_id",
            "subset_split_id",
            "subgraph_id",
            "edge.subject_id",
            "edge.object_id",
            "predicate_scores[].predicate_label",
            "predicate_scores[].score",
        ],
        "identity_checks": [
            "raw schema_version must equal h001_open3dsg_raw_dump_v1",
            "record_type must equal open3dsg_raw_prediction",
            "subgraph_id must equal scan_id + '_' + subset_split_id",
            "scan_id must belong to the fixed H001 selected scans",
            "subgraph_id must belong to the fixed H001 validation contexts",
            "edge.subject_id and edge.object_id must be integer 3DSSG object instance ids",
            "subject and object ids must be distinct",
            "subject and object ids must exist in the matching H001 context object set",
            "predicate scores must be finite and must not silently drop object-pair identity",
            "adapter prediction_id must be deterministic from baseline, split, subgraph, subject, object, and predicate",
        ],
        "blocking_failures": [
            "missing raw dump when real adapter/metric execution is requested",
            "raw row outside H001 selected scan/subgraph scope",
            "raw edge endpoint missing from the corresponding H001 object set",
            "non-finite predicate score",
            "duplicate raw identity rows with conflicting scores",
            "adapter output that changes scan_id, subgraph_id, subject_id, object_id, or predicate label",
        ],
        "allowed_nonblocking_warnings": [
            "same-endpoint raw row skipped with an explicit warning before metric export",
            "unsupported predicate family retained in prediction JSONL but excluded from H001 geometry-checkable metric denominator",
        ],
        "claim_boundary": (
            "This checklist freezes raw-dump identity auditing only. It is not Open3DSG metric evidence "
            "until raw dump, prediction JSONL export, geometry join, and metric evaluation all exist."
        ),
    }


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid_jsonl:{line_no}:{exc}")
    return rows, errors


def audit_raw_dump(repo_root: Path, raw_dump_jsonl: Path, scope: dict[str, Any]) -> dict[str, Any]:
    if not raw_dump_jsonl.exists():
        return {
            "status": "raw_dump_missing",
            "path": relpath(repo_root, raw_dump_jsonl),
            "exists": False,
            "row_count": 0,
            "blockers": [f"missing_raw_dump:{relpath(repo_root, raw_dump_jsonl)}"],
        }
    if scope.get("status") != "ready":
        return {
            "status": "blocked_scope_not_ready",
            "path": relpath(repo_root, raw_dump_jsonl),
            "exists": True,
            "row_count": 0,
            "blockers": list(scope.get("blockers", [])),
        }

    rows, parse_errors = read_jsonl(raw_dump_jsonl)
    contexts = set(scope["context_ids"])
    blockers = list(parse_errors)
    warnings: list[str] = []
    pair_keys: set[tuple[str, int, int]] = set()
    schema_counts = Counter()
    record_type_counts = Counter()
    for index, row in enumerate(rows):
        schema_counts[str(row.get("schema_version"))] += 1
        record_type_counts[str(row.get("record_type"))] += 1
        if row.get("schema_version") != RAW_SCHEMA_VERSION:
            blockers.append(f"bad_schema:{index}:{row.get('schema_version')}")
        if row.get("record_type") != "open3dsg_raw_prediction":
            blockers.append(f"bad_record_type:{index}:{row.get('record_type')}")
        subgraph_id = str(row.get("subgraph_id") or f"{row.get('scan_id')}_{row.get('subset_split_id')}")
        expected_subgraph = f"{row.get('scan_id')}_{row.get('subset_split_id')}"
        if subgraph_id != expected_subgraph:
            blockers.append(f"subgraph_id_mismatch:{index}:{subgraph_id}:{expected_subgraph}")
        if subgraph_id not in contexts:
            blockers.append(f"raw_subgraph_not_in_h001_scope:{index}:{subgraph_id}")
        edge = row.get("edge") if isinstance(row.get("edge"), dict) else {}
        try:
            subject_id = int(edge.get("subject_id", row.get("subject_id")))
            object_id = int(edge.get("object_id", row.get("object_id")))
        except (TypeError, ValueError):
            blockers.append(f"bad_edge_ids:{index}:{subgraph_id}")
            continue
        if subject_id == object_id:
            warnings.append(f"same_endpoint:{index}:{subgraph_id}:{subject_id}")
            continue
        pair_keys.add((subgraph_id, subject_id, object_id))

    return {
        "status": STATUS_AUDIT_READY if not blockers else STATUS_AUDIT_BLOCKED,
        "path": relpath(repo_root, raw_dump_jsonl),
        "exists": True,
        "row_count": len(rows),
        "unique_directed_pairs": len(pair_keys),
        "schema_counts": dict(sorted(schema_counts.items())),
        "record_type_counts": dict(sorted(record_type_counts.items())),
        "warnings": warnings[:100],
        "blockers": blockers[:200],
        "truncated": {
            "warnings": len(warnings) > 100,
            "blockers": len(blockers) > 200,
        },
    }


def build_manifest(
    repo_root: Path,
    raw_dump_jsonl: Path,
    predictions_jsonl: Path,
    scope: dict[str, Any],
    raw_audit: dict[str, Any],
) -> dict[str, Any]:
    if raw_dump_jsonl.exists() and raw_audit["status"] == STATUS_AUDIT_READY and scope.get("status") == "ready":
        status = STATUS_AUDIT_READY
    elif not raw_dump_jsonl.exists() and scope.get("status") == "ready":
        status = STATUS_READY_MISSING
    else:
        status = STATUS_AUDIT_BLOCKED
    blockers: list[str] = []
    blockers.extend(scope.get("blockers", []))
    blockers.extend(raw_audit.get("blockers", []))
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": status,
        "scope": scope,
        "raw_dump": raw_audit,
        "predictions_jsonl": {
            "path": relpath(repo_root, predictions_jsonl),
            "exists": predictions_jsonl.exists(),
            "status": "present" if predictions_jsonl.exists() else "missing_until_raw_dump_adapter_runs",
        },
        "blockers": blockers,
        "next_action_after_raw_dump": (
            "Run this identity audit before open3dsg_adapter_raw_dump; adapter output must preserve scan, "
            "subgraph, subject, object, and predicate identity."
        ),
    }


def build_commands(raw_dump_jsonl: Path, repo_root: Path) -> str:
    raw_rel = relpath(repo_root, raw_dump_jsonl)
    return f"""# Open3DSG Raw-Dump Identity Commands

Freeze or refresh the raw-dump identity checklist:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity'
```

After a real raw dump exists, rerun the same command, then convert the raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/{raw_rel} docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump'
```

Do not run Open3DSG metric/join until raw-dump identity audit and adapter export both pass.
"""


def build_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Raw-Dump Identity Audit",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Fact",
        "",
        "- This artifact freezes the raw-dump identity checklist before Open3DSG raw outputs exist.",
        "- It does not run Open3DSG eval, convert predictions, inspect metrics, or assign failure labels.",
        "- The fixed H001 eval scope is used as the identity denominator.",
        "",
        "## Scope",
        "",
        f"- selected scans: `{payload['scope'].get('selected_scans')}/{EXPECTED_SCANS}`",
        f"- contexts: `{payload['scope'].get('contexts')}/{EXPECTED_CONTEXTS}`",
        f"- directed pairs: `{payload['scope'].get('directed_pairs')}/{EXPECTED_DIRECTED_PAIRS}`",
        "",
        "## Raw Dump",
        "",
        f"- path: `{payload['raw_dump']['path']}`",
        f"- status: `{payload['raw_dump']['status']}`",
        f"- rows: `{payload['raw_dump']['row_count']}`",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This is checklist/audit readiness only. It is not Open3DSG metric evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    raw_dump_jsonl = resolve(repo_root, args.raw_dump_jsonl)
    predictions_jsonl = resolve(repo_root, args.predictions_jsonl)
    subset_json = resolve(repo_root, args.subset_json)
    selected_scans = resolve(repo_root, args.selected_scans)
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    scope = build_scope(repo_root, subset_json, selected_scans)
    raw_audit = audit_raw_dump(repo_root, raw_dump_jsonl, scope)
    payload = build_manifest(repo_root, raw_dump_jsonl, predictions_jsonl, scope, raw_audit)

    write_json(out_dir / "checklist.json", checklist())
    write_json(out_dir / "manifest.json", payload)
    (out_dir / "commands.md").write_text(build_commands(raw_dump_jsonl, repo_root), encoding="utf-8")
    (out_dir / "report.md").write_text(build_report(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "raw_dump_status": raw_audit["status"],
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
