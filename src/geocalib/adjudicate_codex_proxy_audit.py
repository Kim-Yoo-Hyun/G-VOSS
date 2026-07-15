#!/usr/bin/env python3
"""Create a complete, non-human Codex proxy reference from two blind passes.

The two input passes were locked before comparison.  This script combines their
438 exact agreements with an evidence-only visual adjudication of every row
triggered by disagreement, low confidence, ambiguity, or unobservability.  It
never reads the private sampling/ranking sidecar.  The output is an automatic
proxy reference for external review, not a human annotation.
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

from PIL import Image, ImageDraw


LABELS = {"physically_valid", "physically_invalid", "ambiguous", "unobservable"}
ALLOWED_REASONS = {
    "geometry_supports_relation",
    "contact_or_support_missing",
    "distance_inconsistent",
    "vertical_order_inconsistent",
    "predicate_semantically_underspecified",
    "segmentation_or_reconstruction_issue",
    "occlusion_or_insufficient_evidence",
    "other",
}

# Evidence-only adjudication after inspecting the 50 disagreement projections.
# No source identity, score, rank, verifier result, GT membership, stratum, or
# method condition was available during these decisions.
DISAGREEMENT_DECISIONS: dict[str, tuple[str, str]] = {
    "PV-0001": ("physically_invalid", "visible pair geometry does not support the stated ceiling contact/support configuration"),
    "PV-0009": ("physically_invalid", "visible pair geometry does not support the stated ceiling contact/support configuration"),
    "PV-0019": ("ambiguous", "floor contact is plausible but the standing-versus-lying pose subtype is not resolved"),
    "PV-0022": ("ambiguous", "the vertical extents overlap and do not yield a stable instance-level higher-than judgment"),
    "PV-0049": ("ambiguous", "floor proximity is visible but the lying pose subtype is not resolved"),
    "PV-0058": ("physically_invalid", "the window is separated from the floor support surface in the visible projections"),
    "PV-0071": ("physically_valid", "the cabinet and chair are adjacent at a small separation relative to their extents"),
    "PV-0072": ("ambiguous", "the towel-curtain separation is near a context-dependent close-by boundary"),
    "PV-0113": ("ambiguous", "the table-radiator separation is plausible but context-dependent for close by"),
    "PV-0141": ("physically_invalid", "the table lamp does not provide a visible support configuration for the chair"),
    "PV-0144": ("physically_valid", "the couch table and cabinet are visibly adjacent relative to their extents"),
    "PV-0145": ("ambiguous", "floor contact is plausible but the television pose does not establish lying on"),
    "PV-0146": ("physically_invalid", "the directed floor-standing-on-shelf relation is contradicted by the pair geometry"),
    "PV-0156": ("physically_invalid", "the directed floor-lying-on-lamp relation is contradicted by the pair geometry"),
    "PV-0158": ("physically_invalid", "the pack is separated from and below the microwave rather than lying on it"),
    "PV-0178": ("ambiguous", "cabinet-counter contact is plausible but the standing subtype is semantically indeterminate"),
    "PV-0184": ("ambiguous", "floor contact is plausible but the pillow standing subtype is not visually determined"),
    "PV-0198": ("physically_invalid", "the wall is vertically oriented and is not visibly lying on the floor"),
    "PV-0204": ("physically_invalid", "the cupboard and ottoman are separated without visible lying contact"),
    "PV-0211": ("physically_invalid", "the table stands on the floor; the stated inverse support direction is contradicted"),
    "PV-0212": ("ambiguous", "the two shelf instances overlap but the directed support relation is not identifiable"),
    "PV-0232": ("physically_valid", "the plant and shelf are visibly adjacent at a small relative separation"),
    "PV-0242": ("physically_valid", "the subject object is visibly above the couch across vertical projections"),
    "PV-0262": ("physically_invalid", "the decoration is separated from the shelf without visible standing contact"),
    "PV-0263": ("ambiguous", "the cleanser-washing-machine distance is near a scale- and context-dependent boundary"),
    "PV-0282": ("physically_invalid", "the clothes dryer lacks visible standing contact with the shelf"),
    "PV-0298": ("physically_valid", "the trash can has a clear upright floor-support configuration"),
    "PV-0319": ("ambiguous", "the two shelf instances are separated near a context-dependent close-by boundary"),
    "PV-0338": ("ambiguous", "pillow-blanket contact is plausible but a standing pose is not identifiable"),
    "PV-0347": ("physically_valid", "the towel is adjacent to the wall with negligible relative separation"),
    "PV-0352": ("ambiguous", "sparse reconstruction leaves the folder-box close-by boundary indeterminate"),
    "PV-0361": ("physically_invalid", "the lamp does not visibly support the shower wall"),
    "PV-0368": ("physically_invalid", "the pillow is visibly separated above the floor rather than lying on it"),
    "PV-0369": ("physically_invalid", "the ceiling-wall configuration does not support the stated standing-on predicate"),
    "PV-0372": ("physically_invalid", "the chair is supported by the floor; the stated inverse lying relation is contradicted"),
    "PV-0378": ("ambiguous", "possible wall attachment cannot be distinguished from separation in the available views"),
    "PV-0387": ("physically_invalid", "the wall is not visibly lying on the sink"),
    "PV-0388": ("physically_valid", "the plant is in direct proximity to the floor surface"),
    "PV-0408": ("physically_valid", "the floor is visibly below the curtain"),
    "PV-0415": ("ambiguous", "the lamp is adjacent to or attached to the wall, but lying-on semantics are indeterminate"),
    "PV-0421": ("physically_valid", "the two bath-cabinet instances are visibly adjacent"),
    "PV-0428": ("ambiguous", "segmentation and relative separation make clutter-close-by-floor indeterminate"),
    "PV-0433": ("physically_valid", "the floor is visibly below the radiator"),
    "PV-0434": ("physically_invalid", "the cabinet stands on the floor; the stated inverse standing direction is contradicted"),
    "PV-0436": ("physically_invalid", "the blanket lies on the floor; the stated inverse lying direction is contradicted"),
    "PV-0447": ("physically_invalid", "the lamp instances are separated above the bench without visible support contact"),
    "PV-0460": ("physically_valid", "the table is visibly adjacent to the wall"),
    "PV-0466": ("physically_invalid", "the wall is vertically oriented rather than lying on the floor"),
    "PV-0478": ("physically_invalid", "the cleanser is separated from the doorframe relative to its extent"),
    "PV-0480": ("physically_valid", "the two wall instances are adjacent/intersecting in the visible geometry"),
}

# Both blind passes marked these rows low-confidence ambiguous.  Full mandatory
# adjudication of the projection sheets found a visible directional or support
# contradiction.  The locked first-pass files remain unchanged.
AGREED_LOW_CONFIDENCE_DECISIONS: dict[str, tuple[str, str]] = {
    "PV-0016": ("physically_invalid", "the sofa is not supported by the small plate instance in the visible geometry"),
    "PV-0066": ("physically_invalid", "the horizontal floor does not stand on the vertical wall"),
    "PV-0109": ("physically_invalid", "the floor is not lying on or supported by the heater"),
    "PV-0164": ("physically_invalid", "the cabinet is visibly separated below the ceiling rather than supported by it"),
    "PV-0180": ("physically_invalid", "the horizontal floor does not stand on the vertical wall"),
    "PV-0223": ("physically_invalid", "the floor is visibly below rather than higher than the ottoman"),
    "PV-0230": ("physically_invalid", "the shelf is visibly above rather than lower than the television"),
    "PV-0253": ("physically_invalid", "the subject cabinet is visibly above rather than lower than the object cabinet"),
    "PV-0283": ("physically_invalid", "the wall is separated from and not supported by the pillow"),
    "PV-0288": ("physically_invalid", "the couch is visibly above rather than lower than the floor"),
    "PV-0297": ("physically_invalid", "the floor lies below the shower curtain and does not stand on it"),
    "PV-0309": ("physically_invalid", "the ceiling is vertically separated from and not supported by the floor"),
    "PV-0323": ("physically_invalid", "the sink is visibly separated above the floor without standing contact"),
    "PV-0329": ("physically_invalid", "the floor is visibly below rather than higher than the sofa"),
    "PV-0344": ("physically_invalid", "the television stand is not supported by the curtain"),
    "PV-0351": ("physically_invalid", "the plant is upright above the fireplace rather than lying on it"),
    "PV-0363": ("physically_invalid", "the doorframe is below and separated from the ceiling rather than standing on it"),
    "PV-0364": ("physically_invalid", "the light is visibly above rather than lower than the plant"),
    "PV-0396": ("physically_invalid", "the bed is not supported by the small separated picture instance"),
    "PV-0405": ("physically_invalid", "the stool is not supported by the plant in the visible geometry"),
    "PV-0430": ("physically_invalid", "the chair is upright on the floor rather than lying on it"),
    "PV-0462": ("physically_invalid", "the floor lies below the sink and does not stand on it"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--public-queue", type=Path, required=True)
    parser.add_argument("--pass-v1", type=Path, required=True)
    parser.add_argument("--pass-v2", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
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
    return {row["audit_id"]: row for row in rows}


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    return {row["audit_id"]: row for row in rows}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_mandatory_sheets(root: Path, rows: list[dict[str, Any]], out: Path) -> list[Path]:
    """Render the complete mandatory-adjudication queue in ten-item sheets."""
    sheet_dir = out / "mandatory_adjudication_sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for sheet_index, start in enumerate(range(0, len(rows), 10), 1):
        batch = rows[start : start + 10]
        canvas = Image.new("RGB", (1400, 1280), "white")
        draw = ImageDraw.Draw(canvas)
        for local_index, row in enumerate(batch):
            col = local_index % 2
            line = local_index // 2
            x, y = col * 700, line * 256
            source = resolve(root, Path(row["geometry_projection_path"]))
            with Image.open(source) as image:
                image = image.convert("RGB")
                image.thumbnail((690, 214))
                canvas.paste(image, (x + 5, y + 36))
            labels = (
                f"v1={row['pass_v1_label'].replace('physically_', '')}  "
                f"v2={row['pass_v2_label'].replace('physically_', '')}  "
                f"final={row['adjudicated_label'].replace('physically_', '')}"
            )
            draw.text((x + 8, y + 5), f"{row['audit_id']}  {labels}", fill="black")
            draw.text((x + 8, y + 19), row["relation"][:105], fill="black")
        path = sheet_dir / f"sheet_{sheet_index:02d}.jpg"
        canvas.save(path, quality=95)
        paths.append(path)
    return paths


def external_review_guide() -> str:
    return """# External Verification Guide

This is verification of a completed Codex proxy reference, not an independent
first-pass annotation task. Each reviewer receives one `external_reviewer_N.csv`
file and checks all 488 rows using the relation text, geometry projection,
optional RGB crop, and pair PLY.

For every row:

- use `verdict=confirm` and leave `corrected_label` empty when the proxy label is
  acceptable;
- use `verdict=revise`, enter one of `physically_valid`, `physically_invalid`,
  `ambiguous`, or `unobservable`, and provide a nonempty `comment` when changing
  the label;
- use one pseudonymous `reviewer_id` throughout the sheet and an ISO-8601
  `reviewed_at` timestamp on every row;
- do not edit, delete, add, or reorder immutable columns or rows.

The three sheets must use distinct reviewer IDs. After all sheets are returned,
run `external_proxy_review_validate`. A row is accepted only when at least two
reviewers agree; the validator writes the reviewer-verified proxy reference.
The resulting evidence must be described as reviewer-verified LLM annotation,
not as independent human first-pass annotation or human ground truth.
"""


def reason_for(label: str, family: str) -> str:
    if label == "physically_valid":
        return "geometry_supports_relation"
    if label == "ambiguous":
        return "predicate_semantically_underspecified"
    if label == "unobservable":
        return "occlusion_or_insufficient_evidence"
    return {
        "support_contact": "contact_or_support_missing",
        "proximity": "distance_inconsistent",
        "relative_vertical": "vertical_order_inconsistent",
    }[family]


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {
        "public_queue": resolve(root, args.public_queue),
        "pass_v1": resolve(root, args.pass_v1),
        "pass_v2": resolve(root, args.pass_v2),
    }
    out = resolve(root, args.out)
    public, pass1, pass2 = read_jsonl(paths["public_queue"]), read_csv(paths["pass_v1"]), read_csv(paths["pass_v2"])
    expected = set(public)
    if set(pass1) != expected or set(pass2) != expected or len(expected) != 488:
        raise ValueError("audit_id_contract_failed")
    disagreement_ids = {audit_id for audit_id in expected if pass1[audit_id]["physical_validity_label"] != pass2[audit_id]["physical_validity_label"]}
    if disagreement_ids != set(DISAGREEMENT_DECISIONS) or len(disagreement_ids) != 50:
        raise ValueError("manual_adjudication_set_mismatch")

    created_at = datetime.now(timezone.utc).isoformat()
    reference_rows: list[dict[str, Any]] = []
    adjudication_rows: list[dict[str, Any]] = []
    verification_rows: list[dict[str, Any]] = []
    rgb_rows_available = 0
    for audit_id in sorted(expected):
        item, a, b = public[audit_id], pass1[audit_id], pass2[audit_id]
        label_a, label_b = a["physical_validity_label"], b["physical_validity_label"]
        mandatory = (
            label_a != label_b
            or a["confidence"] == "low"
            or b["confidence"] == "low"
            or label_a in {"ambiguous", "unobservable"}
            or label_b in {"ambiguous", "unobservable"}
        )
        if audit_id in AGREED_LOW_CONFIDENCE_DECISIONS:
            if label_a != "ambiguous" or label_b != "ambiguous" or not mandatory:
                raise ValueError(f"agreed_low_confidence_contract_failed:{audit_id}")
            label, note = AGREED_LOW_CONFIDENCE_DECISIONS[audit_id]
            decision_basis = "evidence_only_visual_adjudication"
        elif label_a == label_b:
            label = label_a
            if mandatory:
                decision_basis = "evidence_only_visual_adjudication"
                note = "Mandatory evidence-only adjudication confirmed the agreed four-class proxy label."
            else:
                decision_basis = "exact_two_pass_agreement"
                note = "Both independently locked Codex blind passes selected the same four-class label."
        else:
            label, note = DISAGREEMENT_DECISIONS[audit_id]
            decision_basis = "evidence_only_visual_adjudication"
        if label not in LABELS:
            raise ValueError(f"invalid_final_label:{audit_id}:{label}")
        family = item["predicate_family"]
        rgb_path = item["rgb_pair_crop_path"]
        if rgb_path and resolve(root, Path(rgb_path)).is_file():
            rgb_rows_available += 1
        else:
            rgb_path = ""
        reason = reason_for(label, family)
        if reason not in ALLOWED_REASONS:
            raise ValueError(f"invalid_reason:{audit_id}:{reason}")
        confidence = "low" if label in {"ambiguous", "unobservable"} else (
            "high" if a["confidence"] == b["confidence"] == "high" else "medium"
        )
        evidence_sufficient = "false" if label == "unobservable" else "true"
        reference_rows.append({
            "audit_id": audit_id,
            "relation": item["relation"],
            "predicate_label": item["predicate_label"],
            "predicate_family": family,
            "rgb_pair_crop_path": rgb_path,
            "geometry_projection_path": item["geometry_projection_path"],
            "pair_ply_path": item["pair_ply_path"],
            "physical_validity_label": label,
            "confidence": confidence,
            "primary_reason_code": reason,
            "evidence_sufficient": evidence_sufficient,
            "decision_basis": decision_basis,
            "notes": note,
            "reviewer_id": "codex_blinded_proxy_adjudication_v1",
            "reviewed_at": created_at,
        })
        if mandatory:
            triggers = []
            if label_a != label_b:
                triggers.append("label_disagreement")
            if a["confidence"] == "low" or b["confidence"] == "low":
                triggers.append("low_confidence")
            if label_a in {"ambiguous", "unobservable"} or label_b in {"ambiguous", "unobservable"}:
                triggers.append("ambiguous_or_unobservable")
            adjudication_rows.append({
                "audit_id": audit_id,
                "relation": item["relation"],
                "predicate_family": family,
                "geometry_projection_path": item["geometry_projection_path"],
                "pass_v1_label": label_a,
                "pass_v2_label": label_b,
                "triggers": ";".join(triggers),
                "adjudicated_label": label,
                "adjudication_reason": note,
                "adjudicator_id": "codex_blinded_proxy_adjudication_v1",
                "adjudicated_at": created_at,
            })
        verification_rows.append({
            "audit_id": audit_id,
            "relation": item["relation"],
            "predicate_family": family,
            "rgb_pair_crop_path": rgb_path,
            "geometry_projection_path": item["geometry_projection_path"],
            "pair_ply_path": item["pair_ply_path"],
            "proxy_label": label,
            "proxy_confidence": confidence,
            "proxy_reason": note,
            "verdict": "",
            "corrected_label": "",
            "comment": "",
            "reviewer_id": "",
            "reviewed_at": "",
        })

    if len(reference_rows) != 488 or len(adjudication_rows) != 154:
        raise ValueError("completion_count_failed")
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "reference.csv", reference_rows)
    write_csv(out / "adjudication.csv", adjudication_rows)
    mandatory_sheets = make_mandatory_sheets(root, adjudication_rows, out)
    for reviewer_index in (1, 2, 3):
        write_csv(out / f"external_reviewer_{reviewer_index}.csv", verification_rows)
    (out / "external_review_guide.md").write_text(external_review_guide(), encoding="utf-8")
    label_counts = Counter(row["physical_validity_label"] for row in reference_rows)
    family_counts = {
        family: dict(sorted(Counter(
            row["physical_validity_label"] for row in reference_rows if row["predicate_family"] == family
        ).items()))
        for family in ("support_contact", "proximity", "relative_vertical")
    }
    summary = {
        "schema_version": "h001_codex_blinded_proxy_reference_v1",
        "created_at_utc": created_at,
        "status": "completed_nonhuman_proxy_reference_awaiting_external_verification",
        "rows": 488,
        "two_pass_exact_agreements": 438,
        "visually_adjudicated_disagreements": 50,
        "visually_adjudicated_agreed_low_confidence_revisions": len(AGREED_LOW_CONFIDENCE_DECISIONS),
        "mandatory_adjudication_rows_completed": 154,
        "mandatory_adjudication_sheets": [relpath(root, path) for path in mandatory_sheets],
        "evidence_coverage": {
            "geometry_projection": 488,
            "pair_ply": 488,
            "optional_rgb_pair_crop_currently_available": rgb_rows_available,
        },
        "label_counts": dict(sorted(label_counts.items())),
        "label_counts_by_family": family_counts,
        "blinding": {
            "used": ["relation text", "raw orthographic point projections"],
            "provided_for_external_verification": ["raw orthographic point projections", "colored pair PLY path", "RGB pair crop only when currently available"],
            "excluded_until_reference_lock": ["source identity", "source score", "compatibility score", "rank", "verifier result", "GT membership", "sampling stratum", "method condition", "private sidecar"],
        },
        "claim_boundary": "A complete Codex blinded proxy reference. It is not independent human evidence and becomes reviewer-verified only after all three external review sheets are completed and validated.",
    }
    write_json(out / "summary.json", summary)
    (out / "summary.md").write_text(
        "# Codex Blinded Proxy Reference\n\n"
        f"Status: `{summary['status']}`\n\n"
        "- Rows: 488/488\n"
        "- Exact two-pass agreements: 438\n"
        "- Evidence-only visual disagreement adjudications: 50/50\n"
        "- Mandatory adjudication review queue: 154/154 rows in 16 sheets\n"
        f"- Agreed low-confidence labels revised after visual adjudication: {len(AGREED_LOW_CONFIDENCE_DECISIONS)}\n"
        f"- Final labels: `{dict(sorted(label_counts.items()))}`\n\n"
        "This is a non-human automatic proxy reference. Three external reviewers receive the completed labels for verification, not a blank annotation task.\n",
        encoding="utf-8",
    )
    outputs = [
        "reference.csv",
        "adjudication.csv",
        "external_reviewer_1.csv",
        "external_reviewer_2.csv",
        "external_reviewer_3.csv",
        "external_review_guide.md",
        "summary.json",
        "summary.md",
    ]
    outputs.extend(str(path.relative_to(out)) for path in mandatory_sheets)
    write_json(out / "manifest.json", {
        "schema_version": "h001_codex_blinded_proxy_reference_manifest_v1",
        "status": summary["status"],
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256(path)} for name, path in paths.items()},
        "outputs": {name: {"path": relpath(root, out / name), "sha256": sha256(out / name)} for name in outputs},
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_adjudicate",
        "claim_boundary": summary["claim_boundary"],
    })
    print(json.dumps({"status": summary["status"], "out": relpath(root, out), "labels": dict(label_counts)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
