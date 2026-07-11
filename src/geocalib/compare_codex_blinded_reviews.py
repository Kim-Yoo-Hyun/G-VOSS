#!/usr/bin/env python3
"""Compare two locked Codex blinded audit passes after both decision locks."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


LABELS = ("physically_valid", "physically_invalid", "ambiguous", "unobservable")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def cohen_kappa(v1: list[str], v2: list[str]) -> float:
    n = len(v1)
    observed = sum(a == b for a, b in zip(v1, v2)) / n
    c1, c2 = Counter(v1), Counter(v2)
    expected = sum((c1[label] / n) * (c2[label] / n) for label in LABELS)
    return (observed - expected) / (1.0 - expected) if expected < 1.0 else 1.0


def make_sheets(root: Path, rows: list[dict[str, Any]], out: Path) -> list[str]:
    sheet_dir = out / "disagreement_sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
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
                image.thumbnail((690, 224))
                canvas.paste(image, (x + 5, y + 26))
            title = (
                f"{row['audit_id']}  v1={row['pass_v1_label'].replace('physically_', '')}  "
                f"v2={row['pass_v2_label'].replace('physically_', '')}"
            )
            draw.text((x + 8, y + 6), title, fill="black")
        path = sheet_dir / f"sheet_{sheet_index:02d}.jpg"
        canvas.save(path, quality=95)
        paths.append(relpath(root, path))
    return paths


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    path1, path2 = resolve(root, args.pass_v1), resolve(root, args.pass_v2)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    pass1, pass2 = read_csv(path1), read_csv(path2)
    if set(pass1) != set(pass2) or len(pass1) != 488:
        raise ValueError("pass_identity_mismatch")
    ordered = sorted(pass1)
    labels1 = [pass1[key]["physical_validity_label"] for key in ordered]
    labels2 = [pass2[key]["physical_validity_label"] for key in ordered]
    confusion = Counter(zip(labels1, labels2))
    disagreements: list[dict[str, Any]] = []
    direct_polarity_flips = 0
    by_family: dict[str, Counter[str]] = {}
    by_predicate: dict[str, Counter[str]] = {}
    for key in ordered:
        a, b = pass1[key], pass2[key]
        label1, label2 = a["physical_validity_label"], b["physical_validity_label"]
        family = a["predicate_family"]
        predicate = a["predicate_label"]
        by_family.setdefault(family, Counter())["rows"] += 1
        by_predicate.setdefault(predicate, Counter())["rows"] += 1
        same = label1 == label2
        by_family[family]["agreement"] += int(same)
        by_predicate[predicate]["agreement"] += int(same)
        if same:
            continue
        if {label1, label2} == {"physically_valid", "physically_invalid"}:
            direct_polarity_flips += 1
        disagreements.append(
            {
                "audit_id": key,
                "relation": a["relation"],
                "predicate_family": family,
                "predicate_label": predicate,
                "geometry_projection_path": a["geometry_projection_path"],
                "rgb_pair_crop_path": a["rgb_pair_crop_path"],
                "pass_v1_label": label1,
                "pass_v1_confidence": a["confidence"],
                "pass_v1_reason": a["primary_reason_code"],
                "pass_v2_label": label2,
                "pass_v2_confidence": b["confidence"],
                "pass_v2_reason": b["primary_reason_code"],
                "transition": f"{label1}->{label2}",
            }
        )
    binary_ids = [
        key
        for key in ordered
        if pass1[key]["physical_validity_label"] in {"physically_valid", "physically_invalid"}
        and pass2[key]["physical_validity_label"] in {"physically_valid", "physically_invalid"}
    ]
    agreement = sum(a == b for a, b in zip(labels1, labels2))
    sheets = make_sheets(root, disagreements, out)
    payload = {
        "schema_version": "h001_codex_blinded_review_comparison_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "locked_passes_compared_visual_followup_pending",
        "counts": {
            "rows": len(ordered),
            "agreement": agreement,
            "disagreement": len(disagreements),
            "agreement_rate": agreement / len(ordered),
            "cohen_kappa_4class": cohen_kappa(labels1, labels2),
            "direct_valid_invalid_flips": direct_polarity_flips,
            "binary_resolved_in_both": len(binary_ids),
            "binary_resolved_agreement": sum(
                pass1[key]["physical_validity_label"] == pass2[key]["physical_validity_label"]
                for key in binary_ids
            ),
        },
        "pass_v1_label_counts": dict(sorted(Counter(labels1).items())),
        "pass_v2_label_counts": dict(sorted(Counter(labels2).items())),
        "confusion_v1_rows_v2_columns": {
            a: {b: confusion[(a, b)] for b in LABELS} for a in LABELS
        },
        "agreement_by_family": {
            key: {
                "rows": value["rows"],
                "agreement": value["agreement"],
                "agreement_rate": value["agreement"] / value["rows"],
            }
            for key, value in sorted(by_family.items())
        },
        "agreement_by_predicate": {
            key: {
                "rows": value["rows"],
                "agreement": value["agreement"],
                "agreement_rate": value["agreement"] / value["rows"],
            }
            for key, value in sorted(by_predicate.items())
        },
        "visual_followup": {
            "scope": "all 50 disagreement rows; no label mutation",
            "contact_sheets": sheets,
        },
        "inputs": {"pass_v1": relpath(root, path1), "pass_v2": relpath(root, path2)},
        "claim_boundary": "same-agent consistency analysis only; not inter-human agreement",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "disagreements.csv", disagreements)
    write_json(out / "comparison.json", payload)
    print(json.dumps({"status": payload["status"], "counts": payload["counts"], "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
