#!/usr/bin/env python3
"""Validate three external reviews of the completed Codex proxy reference.

Each reviewer checks the already completed reference.  A row is either
``confirm`` or ``revise``; revised rows require a corrected four-class label.
The script never silently converts this workflow into independent annotation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LABELS = {"physically_valid", "physically_invalid", "ambiguous", "unobservable"}
VERDICTS = {"confirm", "revise"}
IMMUTABLE = (
    "audit_id", "relation", "predicate_family", "rgb_pair_crop_path",
    "geometry_projection_path", "pair_ply_path", "proxy_label",
    "proxy_confidence", "proxy_reason",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument(
        "--reviews-dir",
        type=Path,
        help="Completed reviewer sheets; defaults to reference-dir for backward compatibility.",
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return bool(value.strip())
    except ValueError:
        return False


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    reference_dir = resolve(root, args.reference_dir)
    reviews_dir = resolve(root, args.reviews_dir) if args.reviews_dir else reference_dir
    out = resolve(root, args.out)
    reference_rows = read_csv(reference_dir / "reference.csv")
    reference = {row["audit_id"]: row for row in reference_rows}
    expected = set(reference)
    errors: list[str] = []
    reviewer_votes: dict[str, list[str]] = {audit_id: [] for audit_id in expected}
    reviewer_verdicts: dict[str, list[str]] = {audit_id: [] for audit_id in expected}
    reviewer_summaries: list[dict[str, Any]] = []
    reviewer_ids: set[str] = set()
    input_paths = [reviews_dir / f"external_reviewer_{index}.csv" for index in (1, 2, 3)]
    for index, path in enumerate(input_paths, 1):
        rows = read_csv(path)
        by_id = {row.get("audit_id", ""): row for row in rows}
        local_errors: list[str] = []
        ids = [row.get("audit_id", "") for row in rows]
        if len(rows) != 488 or len(set(ids)) != 488 or set(ids) != expected:
            local_errors.append("audit_id_contract_failed")
        ids_seen: set[str] = set()
        revisions = 0
        for audit_id in sorted(expected):
            row = by_id.get(audit_id, {})
            ref = reference[audit_id]
            for field in IMMUTABLE:
                expected_value = ref["physical_validity_label"] if field == "proxy_label" else (
                    ref["confidence"] if field == "proxy_confidence" else (
                        ref["notes"] if field == "proxy_reason" else ref[field]
                    )
                )
                if row.get(field, "") != expected_value:
                    local_errors.append(f"{audit_id}:immutable_changed:{field}")
            verdict = row.get("verdict", "").strip().lower()
            corrected = row.get("corrected_label", "").strip()
            reviewer_id = row.get("reviewer_id", "").strip()
            reviewed_at = row.get("reviewed_at", "").strip()
            if verdict not in VERDICTS:
                local_errors.append(f"{audit_id}:invalid_or_missing_verdict")
                continue
            if verdict == "confirm":
                if corrected:
                    local_errors.append(f"{audit_id}:confirm_must_not_set_corrected_label")
                vote = ref["physical_validity_label"]
            else:
                revisions += 1
                if corrected not in LABELS:
                    local_errors.append(f"{audit_id}:revise_requires_valid_corrected_label")
                    continue
                if not row.get("comment", "").strip():
                    local_errors.append(f"{audit_id}:revise_requires_comment")
                vote = corrected
            if not reviewer_id:
                local_errors.append(f"{audit_id}:missing_reviewer_id")
            else:
                ids_seen.add(reviewer_id)
            if not valid_time(reviewed_at):
                local_errors.append(f"{audit_id}:invalid_or_missing_reviewed_at")
            reviewer_votes[audit_id].append(vote)
            reviewer_verdicts[audit_id].append(verdict)
        if len(ids_seen) != 1:
            local_errors.append("requires_exactly_one_reviewer_id")
        reviewer_ids.update(ids_seen)
        reviewer_summaries.append({
            "reviewer_index": index,
            "reviewer_ids": sorted(ids_seen),
            "revisions": revisions,
            "errors": local_errors,
        })
        errors.extend(f"reviewer_{index}:{error}" for error in local_errors)
    if len(reviewer_ids) != 3:
        errors.append("three_distinct_reviewer_ids_required")

    final_labels: dict[str, str] = {}
    unresolved: list[str] = []
    for audit_id, votes in reviewer_votes.items():
        counts = Counter(votes)
        if len(votes) != 3 or not counts or counts.most_common()[0][1] < 2:
            unresolved.append(audit_id)
        else:
            final_labels[audit_id] = counts.most_common()[0][0]
    if unresolved:
        errors.append(f"unresolved_majority_rows:{len(unresolved)}")
    status = "ready_reviewer_verified_proxy_reference" if not errors else (
        "awaiting_external_reviewer_verification" if all(
            "invalid_or_missing_verdict" in error or "missing_reviewer_id" in error or "invalid_or_missing_reviewed_at" in error or "requires_exactly_one_reviewer_id" in error or "three_distinct_reviewer_ids_required" in error or "unresolved_majority_rows" in error
            for error in errors
        ) else "blocked_invalid_external_verification"
    )
    verified_reference_rows: list[dict[str, Any]] = []
    if status == "ready_reviewer_verified_proxy_reference":
        for audit_id in sorted(expected):
            ref = reference[audit_id]
            votes = reviewer_votes[audit_id]
            verified_reference_rows.append({
                **ref,
                "proxy_original_label": ref["physical_validity_label"],
                "external_vote_1": votes[0],
                "external_vote_2": votes[1],
                "external_vote_3": votes[2],
                "external_majority_label": final_labels[audit_id],
                "external_confirmation_count": sum(
                    verdict == "confirm" for verdict in reviewer_verdicts[audit_id]
                ),
            })
        write_csv(out / "reviewer_verified_reference.csv", verified_reference_rows)

    payload = {
        "schema_version": "h001_external_proxy_review_validation_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reviewers": reviewer_summaries,
        "distinct_reviewer_ids": sorted(reviewer_ids),
        "majority_resolved_rows": len(final_labels),
        "verified_reference_rows": len(verified_reference_rows),
        "unresolved_rows": unresolved,
        "errors": errors,
        "claim_boundary": "Human reviewers verify a completed Codex proxy reference; this is reviewer-verified LLM annotation, not three independent first-pass human annotations.",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "validation.json", payload)
    (out / "summary.md").write_text(
        "# External Review of Codex Proxy Reference\n\n"
        f"Status: `{status}`\n\n"
        f"- Majority-resolved rows: {len(final_labels)}/488\n"
        f"- Distinct reviewer IDs: {len(reviewer_ids)}/3\n"
        f"- Validation errors: {len(errors)}\n\n"
        "This workflow validates completed LLM annotations; it is not independent-human first-pass annotation.\n",
        encoding="utf-8",
    )
    output_paths = [out / "validation.json", out / "summary.md"]
    if verified_reference_rows:
        output_paths.append(out / "reviewer_verified_reference.csv")
    write_json(out / "manifest.json", {
        "schema_version": "h001_external_proxy_review_manifest_v1",
        "status": status,
        "inputs": {
            "reference": {"path": relpath(root, reference_dir / "reference.csv"), "sha256": sha256(reference_dir / "reference.csv")},
            **{f"reviewer_{i}": {"path": relpath(root, path), "sha256": sha256(path)} for i, path in enumerate(input_paths, 1)},
        },
        "outputs": {
            path.name: {"path": relpath(root, path), "sha256": sha256(path)}
            for path in output_paths
        },
        "claim_boundary": payload["claim_boundary"],
    })
    print(json.dumps({"status": status, "majority_resolved_rows": len(final_labels), "errors": len(errors)}))
    return 0 if status in {"ready_reviewer_verified_proxy_reference", "awaiting_external_reviewer_verification"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
