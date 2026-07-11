#!/usr/bin/env python3
"""Explain SGFN exact-label GT coverage without changing the frozen denominator."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


FAMILIES = {"support_contact", "proximity", "relative_vertical"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    predictions = resolve(root, args.predictions)
    ground_truth = resolve(root, args.ground_truth)
    pairs: set[tuple[str, int, int]] = set()
    with predictions.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            pairs.add(
                (
                    row["subgraph_id"],
                    int(row["edge"]["subject_id"]),
                    int(row["edge"]["object_id"]),
                )
            )
    scoped = []
    with ground_truth.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row["predicate_family"] in FAMILIES:
                scoped.append(row)
    missing = [
        row
        for row in scoped
        if (row["subgraph_id"], int(row["subject_id"]), int(row["object_id"])) not in pairs
    ]
    self_rows = [row for row in missing if int(row["subject_id"]) == int(row["object_id"])]
    nonself_rows = [row for row in missing if int(row["subject_id"]) != int(row["object_id"])]
    validations = {
        "frozen_gt_denominator_3972": len(scoped) == 3972,
        "missing_gt_rows_11": len(missing) == 11,
        "all_missing_gt_rows_are_self_relations": len(self_rows) == len(missing),
        "no_nonself_source_pair_missing": len(nonself_rows) == 0,
        "all_missing_labels_supported_by": all(row["predicate_label"] == "supported by" for row in missing),
    }
    payload = {
        "schema_version": "h001_sgfn_adapter_coverage_audit_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "sgfn_coverage_audit_ready" if all(validations.values()) else "blocked_sgfn_coverage_audit",
        "counts": {
            "prediction_directed_pairs": len(pairs),
            "in_scope_gt_rows": len(scoped),
            "covered_gt_rows": len(scoped) - len(missing),
            "missing_gt_rows": len(missing),
            "missing_self_relation_rows": len(self_rows),
            "missing_nonself_rows": len(nonself_rows),
        },
        "missing_by_family_label": {
            f"{family}:{label}": count
            for (family, label), count in sorted(
                Counter((row["predicate_family"], row["predicate_label"]) for row in missing).items()
            )
        },
        "missing_gt_ids": [row["gt_id"] for row in missing],
        "validations": validations,
        "policy": "retain all 3,972 GT rows in recall denominator; synthesize no self-edge prediction",
        "interpretation": "SGFN covers every nonself directed pair; 11 malformed/self supported-by GT rows have no model edge by construction",
    }
    out = resolve(root, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "counts": payload["counts"]}))
    return 0 if payload["status"] == "sgfn_coverage_audit_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
