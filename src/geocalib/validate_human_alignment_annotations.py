#!/usr/bin/env python3
"""Validate frozen human labels and every mandatory adjudication target."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_human_alignment_annotation_validation_v1"
ALLOWED_LABELS = {
    "physically_valid",
    "physically_invalid",
    "ambiguous",
    "unobservable",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_EVIDENCE = {"true", "false"}
ALLOWED_REASON_CODES = {
    "geometry_supports_relation",
    "contact_or_support_missing",
    "distance_inconsistent",
    "vertical_order_inconsistent",
    "predicate_semantically_underspecified",
    "segmentation_or_reconstruction_issue",
    "occlusion_or_insufficient_evidence",
    "other",
}
FORBIDDEN_REVIEWER_TOKENS = {
    "codex",
    "openai",
    "chatgpt",
    "gpt",
    "llm",
    "ai_proxy",
    "proxy_agent",
}
IMMUTABLE_FIELDS = (
    "audit_id",
    "relation",
    "predicate_label",
    "predicate_family",
    "rgb_pair_crop_path",
    "geometry_projection_path",
    "pair_ply_path",
)
FIRST_PASS_FIELDS = (
    "physical_validity_label",
    "confidence",
    "primary_reason_code",
    "evidence_sufficient",
    "notes",
    "reviewer_id",
    "reviewed_at",
)
ADJUDICATION_FIELDS = (
    "annotator_a_label",
    "annotator_b_label",
    "adjudicated_label",
    "adjudication_reason",
    "adjudicator_id",
    "adjudicated_at",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/frozen_v1"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/physical_validity_audit/"
            "human_alignment_validation_v1"
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_timestamp(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def forbidden_reviewer_id(value: str) -> bool:
    lowered = value.casefold()
    return any(token in lowered for token in FORBIDDEN_REVIEWER_TOKENS)


def reason_consistent(label: str, reason: str) -> bool:
    if label == "physically_valid":
        return reason == "geometry_supports_relation"
    if label == "physically_invalid":
        return reason in {
            "contact_or_support_missing",
            "distance_inconsistent",
            "vertical_order_inconsistent",
            "other",
        }
    if label == "ambiguous":
        return reason in {"predicate_semantically_underspecified", "other"}
    if label == "unobservable":
        return reason in {
            "segmentation_or_reconstruction_issue",
            "occlusion_or_insufficient_evidence",
        }
    return False


def first_pass_contract(
    name: str,
    rows: list[dict[str, str]],
    public_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    ids = [row.get("audit_id", "").strip() for row in rows]
    expected_ids = set(public_by_id)
    if len(ids) != len(set(ids)):
        errors.append(f"{name}:duplicate_audit_id")
    if set(ids) != expected_ids:
        errors.append(f"{name}:audit_id_set_mismatch")

    label_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    reviewer_ids: set[str] = set()
    labeled = 0
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        audit_id = row.get("audit_id", "").strip()
        if audit_id:
            by_id[audit_id] = row
        reference = public_by_id.get(audit_id)
        if reference:
            for field in IMMUTABLE_FIELDS:
                if str(row.get(field, "")) != str(reference.get(field, "")):
                    errors.append(f"{name}:{audit_id}:immutable_field_changed:{field}")

        label = row.get("physical_validity_label", "").strip()
        populated = [field for field in FIRST_PASS_FIELDS if row.get(field, "").strip()]
        if not label:
            if populated:
                errors.append(f"{name}:{audit_id}:fields_present_without_label")
            continue
        labeled += 1
        label_counts[label] += 1
        confidence = row.get("confidence", "").strip()
        reason = row.get("primary_reason_code", "").strip()
        evidence = row.get("evidence_sufficient", "").strip()
        notes = row.get("notes", "").strip()
        reviewer_id = row.get("reviewer_id", "").strip()
        reviewed_at = row.get("reviewed_at", "").strip()
        if label not in ALLOWED_LABELS:
            errors.append(f"{name}:{audit_id}:invalid_label:{label}")
        if confidence not in ALLOWED_CONFIDENCE:
            errors.append(f"{name}:{audit_id}:invalid_confidence:{confidence}")
        else:
            confidence_counts[confidence] += 1
        if reason not in ALLOWED_REASON_CODES:
            errors.append(f"{name}:{audit_id}:invalid_reason:{reason}")
        elif label in ALLOWED_LABELS and not reason_consistent(label, reason):
            errors.append(f"{name}:{audit_id}:reason_label_mismatch:{reason}:{label}")
        if evidence not in ALLOWED_EVIDENCE:
            errors.append(f"{name}:{audit_id}:invalid_evidence_sufficient:{evidence}")
        elif (label == "unobservable") != (evidence == "false"):
            errors.append(f"{name}:{audit_id}:evidence_label_mismatch:{evidence}:{label}")
        if reason == "other" and not notes:
            errors.append(f"{name}:{audit_id}:other_requires_notes")
        if not reviewer_id:
            errors.append(f"{name}:{audit_id}:missing_reviewer_id")
        else:
            reviewer_ids.add(reviewer_id)
            if forbidden_reviewer_id(reviewer_id):
                errors.append(f"{name}:{audit_id}:forbidden_proxy_reviewer_id")
        if not parse_timestamp(reviewed_at):
            errors.append(f"{name}:{audit_id}:invalid_or_missing_reviewed_at")

    complete = labeled == len(expected_ids)
    if labeled and len(reviewer_ids) != 1:
        errors.append(f"{name}:requires_exactly_one_reviewer_id")
    return {
        "name": name,
        "rows": len(rows),
        "labeled": labeled,
        "expected": len(expected_ids),
        "complete": complete,
        "reviewer_ids": sorted(reviewer_ids),
        "label_counts": dict(sorted(label_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "errors": errors,
        "by_id": by_id,
    }


def required_adjudication(
    sheet_a: dict[str, Any], sheet_b: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    if not sheet_a["complete"] or not sheet_b["complete"]:
        return {}
    output: dict[str, dict[str, Any]] = {}
    for audit_id in sorted(sheet_a["by_id"]):
        a = sheet_a["by_id"][audit_id]
        b = sheet_b["by_id"][audit_id]
        triggers: list[str] = []
        if a["physical_validity_label"] != b["physical_validity_label"]:
            triggers.append("label_disagreement")
        if a["confidence"] == "low" or b["confidence"] == "low":
            triggers.append("low_confidence")
        if a["physical_validity_label"] in {"ambiguous", "unobservable"} or b[
            "physical_validity_label"
        ] in {"ambiguous", "unobservable"}:
            triggers.append("ambiguous_or_unobservable")
        if triggers:
            output[audit_id] = {"triggers": triggers, "a": a, "b": b}
    return output


def adjudication_contract(
    rows: list[dict[str, str]],
    required: dict[str, dict[str, Any]],
    expected_ids: set[str],
    first_pass_reviewer_ids: set[str],
) -> dict[str, Any]:
    errors: list[str] = []
    ids = [row.get("audit_id", "").strip() for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != expected_ids:
        errors.append("adjudication:audit_id_contract_failed")
    by_id = {row.get("audit_id", "").strip(): row for row in rows}
    completed = 0
    adjudicator_ids: set[str] = set()
    for audit_id, row in by_id.items():
        final_label = row.get("adjudicated_label", "").strip()
        populated = [field for field in ADJUDICATION_FIELDS if row.get(field, "").strip()]
        if audit_id not in required:
            if populated:
                errors.append(f"adjudication:{audit_id}:nonrequired_row_must_remain_blank")
            continue
        target = required[audit_id]
        if not final_label:
            continue
        completed += 1
        if row.get("annotator_a_label", "").strip() != target["a"]["physical_validity_label"]:
            errors.append(f"adjudication:{audit_id}:annotator_a_label_mismatch")
        if row.get("annotator_b_label", "").strip() != target["b"]["physical_validity_label"]:
            errors.append(f"adjudication:{audit_id}:annotator_b_label_mismatch")
        if final_label not in ALLOWED_LABELS:
            errors.append(f"adjudication:{audit_id}:invalid_final_label:{final_label}")
        if not row.get("adjudication_reason", "").strip():
            errors.append(f"adjudication:{audit_id}:missing_reason")
        adjudicator_id = row.get("adjudicator_id", "").strip()
        if not adjudicator_id:
            errors.append(f"adjudication:{audit_id}:missing_adjudicator_id")
        else:
            adjudicator_ids.add(adjudicator_id)
            if adjudicator_id in first_pass_reviewer_ids:
                errors.append(f"adjudication:{audit_id}:adjudicator_not_distinct")
            if forbidden_reviewer_id(adjudicator_id):
                errors.append(f"adjudication:{audit_id}:forbidden_proxy_adjudicator_id")
        if not parse_timestamp(row.get("adjudicated_at", "")):
            errors.append(f"adjudication:{audit_id}:invalid_or_missing_timestamp")
    if completed and len(adjudicator_ids) != 1:
        errors.append("adjudication:requires_exactly_one_adjudicator_id")
    missing = sorted(set(required) - {
        audit_id
        for audit_id, row in by_id.items()
        if row.get("adjudicated_label", "").strip()
    })
    return {
        "required": len(required),
        "completed": completed,
        "missing": missing,
        "adjudicator_ids": sorted(adjudicator_ids),
        "errors": errors,
        "by_id": by_id,
    }


def validate_contract(audit_dir: Path) -> dict[str, Any]:
    public = read_jsonl(audit_dir / "public_queue.jsonl")
    public_by_id = {row["audit_id"]: row for row in public}
    rows_a = read_csv(audit_dir / "annotator_a.csv")
    rows_b = read_csv(audit_dir / "annotator_b.csv")
    rows_adj = read_csv(audit_dir / "adjudication.csv")
    sheet_a = first_pass_contract("annotator_a", rows_a, public_by_id)
    sheet_b = first_pass_contract("annotator_b", rows_b, public_by_id)
    errors = list(sheet_a["errors"] + sheet_b["errors"])
    ids_a = set(sheet_a["reviewer_ids"])
    ids_b = set(sheet_b["reviewer_ids"])
    if sheet_a["complete"] and sheet_b["complete"] and (not ids_a or not ids_b or ids_a & ids_b):
        errors.append("first_pass_reviewer_ids_must_be_distinct")
    required = required_adjudication(sheet_a, sheet_b)
    adjudication = adjudication_contract(
        rows_adj,
        required,
        set(public_by_id),
        ids_a | ids_b,
    )
    errors.extend(adjudication["errors"])
    if errors:
        status = "blocked_invalid_human_annotation_contract"
    elif not sheet_a["complete"] or not sheet_b["complete"]:
        status = "awaiting_independent_human_labels"
    elif adjudication["missing"]:
        status = "awaiting_mandatory_blinded_adjudication"
    else:
        status = "ready"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "expected_rows": len(public_by_id),
        "annotator_a": {key: value for key, value in sheet_a.items() if key != "by_id"},
        "annotator_b": {key: value for key, value in sheet_b.items() if key != "by_id"},
        "required_adjudication": {
            "rows": len(required),
            "trigger_counts": dict(sorted(Counter(
                trigger for value in required.values() for trigger in value["triggers"]
            ).items())),
            "ids": sorted(required),
        },
        "adjudication": {key: value for key, value in adjudication.items() if key != "by_id"},
        "errors": errors,
        "_sheet_a": sheet_a,
        "_sheet_b": sheet_b,
        "_required": required,
        "_adjudication": adjudication,
        "_public_by_id": public_by_id,
    }


def build_human_reference(validation: dict[str, Any]) -> dict[str, str]:
    if validation["status"] != "ready":
        return {}
    output: dict[str, str] = {}
    sheet_a = validation["_sheet_a"]["by_id"]
    required = validation["_required"]
    adjudication = validation["_adjudication"]["by_id"]
    for audit_id in sorted(sheet_a):
        if audit_id in required:
            output[audit_id] = adjudication[audit_id]["adjudicated_label"].strip()
        else:
            output[audit_id] = sheet_a[audit_id]["physical_validity_label"].strip()
    return output


def public_validation_payload(validation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in validation.items() if not key.startswith("_")}


def make_adjudication_queue(validation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for audit_id, target in sorted(validation["_required"].items()):
        public = validation["_public_by_id"][audit_id]
        rows.append(
            {
                "audit_id": audit_id,
                "relation": public["relation"],
                "predicate_label": public["predicate_label"],
                "predicate_family": public["predicate_family"],
                "rgb_pair_crop_path": public["rgb_pair_crop_path"],
                "geometry_projection_path": public["geometry_projection_path"],
                "pair_ply_path": public["pair_ply_path"],
                "mandatory_triggers": ";".join(target["triggers"]),
                "annotator_a_label": target["a"]["physical_validity_label"],
                "annotator_a_confidence": target["a"]["confidence"],
                "annotator_b_label": target["b"]["physical_validity_label"],
                "annotator_b_confidence": target["b"]["confidence"],
                "adjudicated_label": "",
                "adjudication_reason": "",
                "adjudicator_id": "",
                "adjudicated_at": "",
            }
        )
    return rows


def make_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Human Alignment Annotation Validation",
            "",
            f"Status: `{payload['status']}`",
            f"Expected first-pass rows per annotator: `{payload['expected_rows']}`",
            f"Annotator A labeled: `{payload['annotator_a']['labeled']}`",
            f"Annotator B labeled: `{payload['annotator_b']['labeled']}`",
            f"Mandatory adjudication rows: `{payload['required_adjudication']['rows']}`",
            f"Completed adjudication rows: `{payload['adjudication']['completed']}`",
            f"Contract errors: `{len(payload['errors'])}`",
            "",
            "The mandatory set is the union of first-pass label disagreements,",
            "either low-confidence decision, and either ambiguous/unobservable label.",
            "No human-alignment or Human V@K claim is reportable unless status is `ready`.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    audit_dir = resolve(root, args.audit_dir)
    out = resolve(root, args.out)
    validation = validate_contract(audit_dir)
    payload = public_validation_payload(validation)
    payload["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["audit_dir"] = relpath(root, audit_dir)
    queue = make_adjudication_queue(validation)
    queue_fields = [
        "audit_id", "relation", "predicate_label", "predicate_family",
        "rgb_pair_crop_path", "geometry_projection_path", "pair_ply_path",
        "mandatory_triggers", "annotator_a_label", "annotator_a_confidence",
        "annotator_b_label", "annotator_b_confidence", "adjudicated_label",
        "adjudication_reason", "adjudicator_id", "adjudicated_at",
    ]
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "validation.json", payload)
    write_csv(out / "required_adjudication.csv", queue, queue_fields)
    (out / "summary.md").write_text(make_report(payload), encoding="utf-8")
    write_json(
        out / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": payload["created_at_utc"],
            "status": payload["status"],
            "inputs": {
                "audit_dir": relpath(root, audit_dir),
                "annotation_guide": relpath(root, audit_dir / "annotation_guide.md"),
                "sha256": {
                    "annotation_guide": sha256_file(audit_dir / "annotation_guide.md"),
                    "annotator_a": sha256_file(audit_dir / "annotator_a.csv"),
                    "annotator_b": sha256_file(audit_dir / "annotator_b.csv"),
                    "adjudication": sha256_file(audit_dir / "adjudication.csv"),
                },
            },
            "outputs": [
                relpath(root, out / "validation.json"),
                relpath(root, out / "required_adjudication.csv"),
                relpath(root, out / "summary.md"),
            ],
        },
    )
    print(json.dumps({"status": payload["status"], "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
