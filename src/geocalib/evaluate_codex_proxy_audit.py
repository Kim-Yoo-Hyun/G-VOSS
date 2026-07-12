#!/usr/bin/env python3
"""Evaluate two locked Codex blind passes as non-human proxy evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


KS = (5, 10, 20, 50, 100)
SOURCES = ("vlsat_closed_set", "open3dsg_ov_recovery")
METHODS = ("semantic_only", "family_conditional_risk")
BINARY = {"physically_valid", "physically_invalid"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--codex-v1", type=Path, required=True)
    parser.add_argument("--codex-v2", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_labels(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["audit_id"]: row["physical_validity_label"] for row in csv.DictReader(handle)}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {name: resolve(root, value) for name, value in {
        "sidecar": args.sidecar, "codex_v1": args.codex_v1, "codex_v2": args.codex_v2,
    }.items()}
    out = resolve(root, args.out)
    v1, v2 = read_labels(paths["codex_v1"]), read_labels(paths["codex_v2"])
    if set(v1) != set(v2) or len(v1) != 488:
        raise ValueError("locked_pass_id_mismatch")
    consensus = {key: v1[key] if v1[key] == v2[key] else "ambiguous" for key in v1}
    accum: dict[tuple[str, str, int, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    source_records = 0
    with paths["sidecar"].open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            audit_id, label, weight = item["audit_id"], consensus[item["audit_id"]], float(item["design_weight"])
            for record in item["source_records"]:
                source = record["source"]
                if source not in SOURCES:
                    continue
                source_records += 1
                family = record["predicate_family"]
                for method in METHODS:
                    rank = record["ranks"].get(f"global_in_scope:{method}")
                    if not isinstance(rank, int):
                        continue
                    for k in KS:
                        if rank > k:
                            continue
                        for slice_name in ("overall", family):
                            cell = accum[(source, method, k, slice_name)]
                            cell["sampled_rows"] += 1
                            cell["weighted_selected"] += weight
                            if label in BINARY:
                                cell["resolved_rows"] += 1
                                cell["weighted_resolved"] += weight
                                if label == "physically_invalid":
                                    cell["invalid_rows"] += 1
                                    cell["weighted_invalid"] += weight
    metrics: dict[str, Any] = {}
    for source in SOURCES:
        metrics[source] = {}
        for method in METHODS:
            metrics[source][method] = {}
            for k in KS:
                overall = accum[(source, method, k, "overall")]
                resolved = overall["weighted_resolved"]
                selected = overall["weighted_selected"]
                metrics[source][method][str(k)] = {
                    "proxy_violation": overall["weighted_invalid"] / resolved if resolved else None,
                    "binary_resolution_coverage": resolved / selected if selected else None,
                    "sampled_rows": int(overall["sampled_rows"]),
                    "resolved_rows": int(overall["resolved_rows"]),
                    "invalid_rows": int(overall["invalid_rows"]),
                    "family": {
                        family: {
                            "proxy_violation": accum[(source, method, k, family)]["weighted_invalid"] / accum[(source, method, k, family)]["weighted_resolved"]
                            if accum[(source, method, k, family)]["weighted_resolved"] else None,
                            "resolved_rows": int(accum[(source, method, k, family)]["resolved_rows"]),
                        }
                        for family in ("support_contact", "proximity", "relative_vertical")
                    },
                }
    validations = {
        "two_locked_passes_488_rows": len(v1) == len(v2) == 488,
        "direct_valid_invalid_flips_zero": not any({v1[key], v2[key]} == BINARY for key in v1),
        "binary_consensus_rows_334": sum(label in BINARY for label in consensus.values()) == 334,
        "sidecar_source_records_present": source_records > 0,
    }
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": "h001_codex_proxy_audit_evaluation_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completed_nonhuman_proxy_only" if all(validations.values()) else "failed",
        "consensus_policy": "retain exact pass agreement; map every pass disagreement to ambiguous; exclude ambiguous/unobservable from the binary proxy denominator",
        "metrics": metrics,
        "validations": validations,
        "claim_boundary": "Two passes from the same Codex model family are non-human automatic-judge stability evidence. They do not establish independent physical validity or Human Violation@K.",
    }
    write_json(out / "summary.json", summary)
    lines = [
        "# Codex Blind Proxy Audit", "", f"Status: `{summary['status']}`", "",
        "This analysis is intentionally excluded from the submission manuscript.", "",
        "| Source | Method | K | Proxy violation | Resolution coverage | Resolved / sampled |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for source in SOURCES:
        for method in METHODS:
            for k in (10, 50, 100):
                cell = metrics[source][method][str(k)]
                lines.append(
                    f"| {source} | {method} | {k} | {cell['proxy_violation']:.4f} | "
                    f"{cell['binary_resolution_coverage']:.4f} | {cell['resolved_rows']} / {cell['sampled_rows']} |"
                )
    lines.extend(["", "These are design-weighted Codex consensus estimates, not human measurements."])
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "h001_codex_proxy_audit_evaluation_manifest_v1",
        "status": summary["status"],
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256_file(path)} for name, path in paths.items()},
        "outputs": {name: {"path": relpath(root, out / name), "sha256": sha256_file(out / name)} for name in ("summary.json", "summary.md")},
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_audit_evaluate",
        "claim_boundary": summary["claim_boundary"],
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": summary["status"], "out": relpath(root, out)}))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
