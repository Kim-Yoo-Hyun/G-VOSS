#!/usr/bin/env python3
"""Compare locked Codex proxy passes with the frozen adjudicated human reference."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_human_alignment_annotations import (
    ALLOWED_LABELS,
    build_human_reference,
    public_validation_payload,
    validate_contract,
)


SCHEMA_VERSION = "h001_codex_human_alignment_evaluation_v1"
BINARY_LABELS = ("physically_valid", "physically_invalid")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/frozen_v1"),
    )
    parser.add_argument(
        "--codex-v1",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/physical_validity_audit/"
            "codex_proxy_v1/codex_proxy_draft.csv"
        ),
    )
    parser.add_argument(
        "--codex-v2",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/physical_validity_audit/"
            "codex_rereview_v2/labels.csv"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/physical_validity_audit/"
            "codex_human_alignment_v1"
        ),
    )
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row.get("audit_id", "").strip() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate_audit_ids:{path}")
    return {row["audit_id"]: row for row in rows}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cohen_kappa(reference: list[str], predictions: list[str]) -> float | None:
    if not reference:
        return None
    labels = sorted(ALLOWED_LABELS)
    observed = sum(a == b for a, b in zip(reference, predictions)) / len(reference)
    counts_ref = Counter(reference)
    counts_pred = Counter(predictions)
    expected = sum(
        (counts_ref[label] / len(reference)) * (counts_pred[label] / len(reference))
        for label in labels
    )
    return (observed - expected) / (1.0 - expected) if expected < 1.0 else 1.0


def binary_metrics(reference: dict[str, str], proxy: dict[str, dict[str, str]]) -> dict[str, Any]:
    human_binary = [audit_id for audit_id, label in reference.items() if label in BINARY_LABELS]
    common = [
        audit_id for audit_id in human_binary
        if proxy[audit_id]["physical_validity_label"] in BINARY_LABELS
    ]
    confusion = Counter(
        (reference[audit_id], proxy[audit_id]["physical_validity_label"])
        for audit_id in common
    )
    tp = confusion[("physically_invalid", "physically_invalid")]
    fp = confusion[("physically_valid", "physically_invalid")]
    fn = confusion[("physically_invalid", "physically_valid")]
    tn = confusion[("physically_valid", "physically_valid")]
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    return {
        "human_binary_rows": len(human_binary),
        "codex_binary_rows_on_human_binary": len(common),
        "codex_binary_coverage": len(common) / len(human_binary) if human_binary else None,
        "accuracy": (tp + tn) / len(common) if common else None,
        "invalid_precision": precision,
        "invalid_recall": recall,
        "invalid_f1": f1,
        "confusion_human_rows_codex_columns": {
            human: {codex: confusion[(human, codex)] for codex in BINARY_LABELS}
            for human in BINARY_LABELS
        },
    }


def alignment_metrics(
    reference: dict[str, str],
    proxy: dict[str, dict[str, str]],
    public: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ordered = sorted(reference)
    ref_labels = [reference[audit_id] for audit_id in ordered]
    proxy_labels = [proxy[audit_id]["physical_validity_label"] for audit_id in ordered]
    confusion = Counter(zip(ref_labels, proxy_labels))
    by_family: dict[str, Any] = {}
    for family in sorted({public[audit_id]["predicate_family"] for audit_id in ordered}):
        family_reference = {
            audit_id: reference[audit_id]
            for audit_id in ordered
            if public[audit_id]["predicate_family"] == family
        }
        family_ids = sorted(family_reference)
        family_ref = [family_reference[audit_id] for audit_id in family_ids]
        family_pred = [proxy[audit_id]["physical_validity_label"] for audit_id in family_ids]
        by_family[family] = {
            "rows": len(family_ids),
            "four_class_agreement": sum(a == b for a, b in zip(family_ref, family_pred)) / len(family_ids),
            "four_class_kappa": cohen_kappa(family_ref, family_pred),
            "binary": binary_metrics(family_reference, proxy),
        }
    confidence: dict[str, Any] = {}
    for level in ("high", "medium", "low"):
        ids = [audit_id for audit_id in ordered if proxy[audit_id].get("confidence", "").strip().lower() == level]
        binary_ids = [
            audit_id for audit_id in ids
            if reference[audit_id] in BINARY_LABELS
            and proxy[audit_id]["physical_validity_label"] in BINARY_LABELS
        ]
        confidence[level] = {
            "rows": len(ids),
            "four_class_accuracy": (
                sum(reference[audit_id] == proxy[audit_id]["physical_validity_label"] for audit_id in ids) / len(ids)
                if ids else None
            ),
            "binary_common_rows": len(binary_ids),
            "binary_accuracy": (
                sum(reference[audit_id] == proxy[audit_id]["physical_validity_label"] for audit_id in binary_ids) / len(binary_ids)
                if binary_ids else None
            ),
        }
    return {
        "rows": len(ordered),
        "human_label_counts": dict(sorted(Counter(ref_labels).items())),
        "codex_label_counts": dict(sorted(Counter(proxy_labels).items())),
        "four_class_agreement": sum(a == b for a, b in zip(ref_labels, proxy_labels)) / len(ordered),
        "four_class_kappa": cohen_kappa(ref_labels, proxy_labels),
        "four_class_confusion_human_rows_codex_columns": {
            human: {codex: confusion[(human, codex)] for codex in sorted(ALLOWED_LABELS)}
            for human in sorted(ALLOWED_LABELS)
        },
        "binary": binary_metrics(reference, proxy),
        "by_family": by_family,
        "accuracy_by_codex_confidence": confidence,
        "confidence_interpretation": (
            "ordinal diagnostic only; no probability mapping or ECE is inferred from high/medium/low"
        ),
    }


def make_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Codex--Human Alignment Evaluation",
        "",
        f"Status: `{payload['status']}`",
        f"Created at UTC: `{payload['created_at_utc']}`",
        "",
    ]
    if payload["status"] != "ready":
        lines.extend(
            [
                "The adjudicated human reference has not passed the frozen annotation contract.",
                "No Codex--human alignment number is reportable.",
                "",
            ]
        )
        return "\n".join(lines)
    for name in ("codex_v1", "codex_v2"):
        result = payload["alignment"][name]
        lines.extend(
            [
                f"## {name}",
                "",
                f"- Four-class agreement: `{result['four_class_agreement']}`",
                f"- Four-class Cohen kappa: `{result['four_class_kappa']}`",
                f"- Binary coverage: `{result['binary']['codex_binary_coverage']}`",
                f"- Binary accuracy: `{result['binary']['accuracy']}`",
                f"- Invalid precision/recall/F1: `{result['binary']['invalid_precision']}` / "
                f"`{result['binary']['invalid_recall']}` / `{result['binary']['invalid_f1']}`",
                "",
            ]
        )
    lines.extend(
        [
            "These are automatic-judge alignment diagnostics against an independent",
            "adjudicated human reference, not evidence that Codex is a human annotator.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    audit_dir = resolve(root, args.audit_dir)
    path_v1 = resolve(root, args.codex_v1)
    path_v2 = resolve(root, args.codex_v2)
    out = resolve(root, args.out)
    validation = validate_contract(audit_dir)
    reference = build_human_reference(validation)
    codex_v1 = read_csv(path_v1)
    codex_v2 = read_csv(path_v2)
    public = {row["audit_id"]: row for row in validation["_public_by_id"].values()}
    expected_ids = set(public)
    errors: list[str] = []
    for name, proxy in (("codex_v1", codex_v1), ("codex_v2", codex_v2)):
        if set(proxy) != expected_ids:
            errors.append(f"{name}:audit_id_set_mismatch")
        invalid = sorted({row.get("physical_validity_label", "") for row in proxy.values()} - ALLOWED_LABELS)
        if invalid:
            errors.append(f"{name}:invalid_labels:{invalid}")
    if errors:
        status = "blocked_invalid_locked_codex_inputs"
    elif validation["status"] != "ready":
        status = "awaiting_valid_adjudicated_human_reference"
    else:
        status = "ready"
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "annotation_validation": public_validation_payload(validation),
        "errors": errors,
        "alignment": {},
        "claim_boundary": (
            "automatic-judge alignment against an independent adjudicated human reference; "
            "Codex passes remain non-human proxy evidence"
        ),
        "locked_input_sha256": {
            "codex_v1": sha256_file(path_v1),
            "codex_v2": sha256_file(path_v2),
            "annotator_a": sha256_file(audit_dir / "annotator_a.csv"),
            "annotator_b": sha256_file(audit_dir / "annotator_b.csv"),
            "adjudication": sha256_file(audit_dir / "adjudication.csv"),
        },
    }
    if status == "ready":
        payload["alignment"] = {
            "codex_v1": alignment_metrics(reference, codex_v1, public),
            "codex_v2": alignment_metrics(reference, codex_v2, public),
        }
        agreed_ids = [
            audit_id for audit_id in sorted(reference)
            if codex_v1[audit_id]["physical_validity_label"]
            == codex_v2[audit_id]["physical_validity_label"]
        ]
        payload["two_pass_consensus"] = {
            "rows": len(agreed_ids),
            "human_four_class_agreement": (
                sum(
                    reference[audit_id] == codex_v1[audit_id]["physical_validity_label"]
                    for audit_id in agreed_ids
                ) / len(agreed_ids)
                if agreed_ids else None
            ),
            "scope": "descriptive only; no post-hoc label mutation or consensus replacement",
        }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "summary.json", payload)
    (out / "summary.md").write_text(make_report(payload), encoding="utf-8")
    write_json(
        out / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": payload["created_at_utc"],
            "status": status,
            "inputs": {
                "audit_dir": relpath(root, audit_dir),
                "codex_v1": relpath(root, path_v1),
                "codex_v2": relpath(root, path_v2),
                "sha256": payload["locked_input_sha256"],
            },
            "outputs": [relpath(root, out / "summary.json"), relpath(root, out / "summary.md")],
        },
    )
    print(json.dumps({"status": status, "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
