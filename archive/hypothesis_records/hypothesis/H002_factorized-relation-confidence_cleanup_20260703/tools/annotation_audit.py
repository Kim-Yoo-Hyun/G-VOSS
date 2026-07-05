#!/usr/bin/env python3
"""Prepare H002 no-GT rows for visual annotation audit.

This script does not assign final visual labels. It creates a review bundle with
local visual/mesh assets and conservative previsual triage labels.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:  # pragma: no cover - optional artifact rendering
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageOps = None


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/visual_annotation_audit"

QUEUE_INPUTS = [
    H002_ROOT / "artifacts/no_gt_audit/vlsat_queue.jsonl",
    H002_ROOT
    / "artifacts/no_gt_audit/open3dsg_recovery_relaxed_views_min2_queue.jsonl",
]

FINAL_LABEL_OPTIONS = [
    "plausible_unlabeled_relation",
    "annotation_sparsity_likely",
    "source_false_positive",
    "object_pair_mismatch",
    "label_granularity_mismatch",
    "geometry_artifact",
    "uncertain_needs_visual",
]

GENERIC_LABELS = {"item", "object", "clutter", "unknown"}
STRUCTURAL_LABELS = {"wall", "floor", "ceiling", "doorframe", "window", "shower wall"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--render-contact-sheets", action="store_true")
    parser.add_argument(
        "--render-priority",
        choices=["all", "high_rank"],
        default="high_rank",
        help="high_rank renders top50 and top100_only rows only.",
    )
    parser.add_argument("--images-per-object", type=int, default=2)
    return parser.parse_args()


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def repo_rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def safe_slug(value: Any) -> str:
    text = str(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "row"


def crop_score(path: Path) -> tuple[int, float, float, str]:
    name = path.name
    is_crop = 1 if "_croped_" in name or "_cropped_" in name else 0
    score_match = re.search(r"_score_([0-9.]+)", name)
    ratio_match = re.search(r"_ratio_([0-9.]+)", name)
    score = float(score_match.group(1)) if score_match else -1.0
    ratio = float(ratio_match.group(1)) if ratio_match else -1.0
    return (-is_crop, -score, -ratio, name)


def find_instance_images(scan_id: str, instance_id: int, limit: int) -> tuple[list[Path], int]:
    image_dir = SCAN_ROOT / scan_id / "multi_view"
    if not image_dir.exists():
        return [], 0
    candidates = [
        path
        for path in image_dir.glob(f"instance_{instance_id}_class_*")
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    candidates = sorted(candidates, key=crop_score)
    return candidates[:limit], len(candidates)


def scan_asset_paths(scan_id: str) -> dict[str, str | None]:
    scan_dir = SCAN_ROOT / scan_id
    return {
        "scan_dir": repo_rel(scan_dir) if scan_dir.exists() else None,
        "mesh_obj": repo_rel(scan_dir / "mesh.refined.v2.obj")
        if (scan_dir / "mesh.refined.v2.obj").exists()
        else None,
        "instance_ply": repo_rel(scan_dir / "labels.instances.align.annotated.v2.ply")
        if (scan_dir / "labels.instances.align.annotated.v2.ply").exists()
        else None,
        "semseg_json": repo_rel(scan_dir / "semseg.v2.json")
        if (scan_dir / "semseg.v2.json").exists()
        else None,
    }


def review_priority(row: dict[str, Any]) -> str:
    scope = row.get("top_scope")
    if scope == "top50":
        return "P0_top50"
    if scope == "top100_only":
        return "P1_top100_only"
    return "P2_outside_top100"


def infer_previsual_label(row: dict[str, Any]) -> tuple[str, str]:
    family = str(row.get("predicate_family"))
    predicate = str(row.get("predicate_label"))
    match_status = str(row.get("match_status"))
    subject_label = str(row.get("subject_label") or "").lower()
    object_label = str(row.get("object_label") or "").lower()
    matched_predicates = [str(item) for item in row.get("matched_predicates") or []]
    reason_codes = [str(item) for item in row.get("reason_codes") or []]

    if row.get("verification_status") != "satisfied":
        return "geometry_artifact", "geometry verifier status is not satisfied"

    if row.get("subject_id") == row.get("object_id"):
        return "object_pair_mismatch", "subject_id and object_id are identical"

    if subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS:
        return (
            "uncertain_needs_visual",
            "one endpoint has a generic object label; visual identity must be checked",
        )

    if (
        family == "support_contact"
        and predicate in {"standing on", "supported by", "lying on"}
        and subject_label in STRUCTURAL_LABELS
        and object_label in STRUCTURAL_LABELS
    ):
        return (
            "source_false_positive",
            "structural-object support/contact wording is semantically suspicious before visual confirmation",
        )

    if match_status == "pair_has_other_predicate":
        return (
            "label_granularity_mismatch",
            "GT has another predicate on the same object pair: "
            + (", ".join(matched_predicates[:4]) if matched_predicates else "unknown"),
        )

    if family == "proximity":
        return (
            "annotation_sparsity_likely",
            "dense proximity relations are usually under-annotated and geometry is satisfied",
        )

    if family == "relative_vertical":
        return (
            "annotation_sparsity_likely",
            "vertical order relation is geometrically satisfied but absent from exact GT",
        )

    if family == "support_contact":
        if reason_codes:
            return (
                "plausible_unlabeled_relation",
                "support/contact verifier produced satisfied witness codes: "
                + ", ".join(reason_codes[:4]),
            )
        return "uncertain_needs_visual", "support/contact relation needs direct point or image review"

    return "uncertain_needs_visual", "relation family is outside the previsual rule set"


def load_font(size: int):
    if ImageFont is None:
        return None
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def wrapped_lines(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if len(candidate) <= max_chars:
            current.append(word)
            continue
        if current:
            lines.append(" ".join(current))
        current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def draw_wrapped(draw: Any, xy: tuple[int, int], text: str, font: Any, fill: str, max_chars: int) -> int:
    x, y = xy
    line_height = int((font.size if hasattr(font, "size") else 14) * 1.35)
    for line in wrapped_lines(text, max_chars):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def image_tile(path: Path, size: tuple[int, int]) -> Any:
    assert Image is not None and ImageOps is not None
    with Image.open(path) as image:
        image = image.convert("RGB")
        image.thumbnail(size)
        tile = Image.new("RGB", size, "white")
        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2
        tile.paste(image, (x, y))
        return tile


def render_contact_sheet(
    row: dict[str, Any],
    subject_images: list[Path],
    object_images: list[Path],
    output_path: Path,
) -> None:
    if Image is None or ImageDraw is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1400, 940
    canvas = Image.new("RGB", (width, height), "#f7f7f4")
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(28)
    text_font = load_font(18)
    small_font = load_font(15)

    header = (
        f"{row['source_id']} | {row['subject_label']}({row['subject_id']}) "
        f"- {row['predicate_label']} -> {row['object_label']}({row['object_id']})"
    )
    y = draw_wrapped(draw, (28, 24), header, title_font, "#111111", 78)
    meta = (
        f"scan={row['scan_id']} | rank={row.get('semantic_rank')} "
        f"score={row.get('semantic_score')} | p_geom={row.get('p_geom_valid')} | "
        f"match={row.get('match_status')} | matched={row.get('matched_predicates')}"
    )
    y = draw_wrapped(draw, (28, y + 8), meta, small_font, "#333333", 140)
    triage = (
        f"previsual_label={row['previsual_label']} | reason={row['previsual_reason']}"
    )
    draw_wrapped(draw, (28, y + 6), triage, small_font, "#333333", 140)

    draw.text((28, 170), "Subject views", font=text_font, fill="#111111")
    draw.text((728, 170), "Object views", font=text_font, fill="#111111")
    tile_size = (315, 255)
    positions = [(28, 205), (360, 205), (728, 205), (1060, 205)]
    displayed = [
        ("subject view 1", subject_images[0] if len(subject_images) > 0 else None),
        ("subject view 2", subject_images[1] if len(subject_images) > 1 else None),
        ("object view 1", object_images[0] if len(object_images) > 0 else None),
        ("object view 2", object_images[1] if len(object_images) > 1 else None),
    ]
    for (label, path), pos in zip(displayed, positions):
        if path is None:
            continue
        tile = image_tile(path, tile_size)
        canvas.paste(tile, pos)
        draw.rectangle((pos[0], pos[1], pos[0] + tile_size[0], pos[1] + tile_size[1]), outline="#999999")
        draw.text((pos[0], pos[1] + tile_size[1] + 8), label, font=small_font, fill="#333333")

    notes = [
        "Review checklist:",
        "1. Are subject/object instance labels correct?",
        "2. Is the predicted relation visually or geometrically plausible?",
        "3. Is missing GT likely annotation sparsity, label granularity mismatch, or source error?",
        "4. If object crops are insufficient, inspect mesh/point evidence listed in review_queue.jsonl.",
    ]
    y = 520
    for note in notes:
        y = draw_wrapped(draw, (28, y), note, small_font, "#111111", 135) + 4

    canvas.save(output_path, quality=88)


def should_render(row: dict[str, Any], render_priority: str) -> bool:
    if render_priority == "all":
        return True
    return row.get("top_scope") in {"top50", "top100_only"}


def enrich_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = H002_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    enriched: list[dict[str, Any]] = []
    counters: dict[str, Counter] = {
        "by_source": Counter(),
        "by_family": Counter(),
        "by_priority": Counter(),
        "by_previsual_label": Counter(),
        "by_source_label": Counter(),
        "by_family_label": Counter(),
        "by_asset_state": Counter(),
    }

    input_counts: dict[str, int] = {}
    for queue_path in QUEUE_INPUTS:
        input_counts[str(queue_path.relative_to(H002_ROOT))] = 0
        for _, row in read_jsonl(queue_path):
            input_counts[str(queue_path.relative_to(H002_ROOT))] += 1
            subject_images, subject_image_count = find_instance_images(
                str(row["scan_id"]), int(row["subject_id"]), args.images_per_object
            )
            object_images, object_image_count = find_instance_images(
                str(row["scan_id"]), int(row["object_id"]), args.images_per_object
            )
            previsual_label, previsual_reason = infer_previsual_label(row)
            priority = review_priority(row)
            asset_state = (
                "subject_and_object_images"
                if subject_images and object_images
                else "missing_subject_or_object_images"
            )

            review_row = dict(row)
            review_row.update(
                {
                    "review_priority": priority,
                    "previsual_label": previsual_label,
                    "previsual_reason": previsual_reason,
                    "final_label": None,
                    "requires_visual_confirmation": True,
                    "asset_state": asset_state,
                    "visual_assets": {
                        **scan_asset_paths(str(row["scan_id"])),
                        "subject_images": [repo_rel(path) for path in subject_images],
                        "object_images": [repo_rel(path) for path in object_images],
                        "subject_image_count": subject_image_count,
                        "object_image_count": object_image_count,
                        "contact_sheet": None,
                    },
                }
            )

            if args.render_contact_sheets and should_render(review_row, args.render_priority):
                sheet_name = (
                    f"{len(enriched) + 1:04d}_{safe_slug(row['source_id'])}_"
                    f"{safe_slug(str(row['scan_id'])[:8])}_{row['subject_id']}_"
                    f"{safe_slug(row['predicate_label'])}_{row['object_id']}.jpg"
                )
                sheet_path = output_dir / "contact_sheets" / sheet_name
                if subject_images and object_images:
                    render_contact_sheet(review_row, subject_images, object_images, sheet_path)
                    review_row["visual_assets"]["contact_sheet"] = repo_rel(sheet_path)

            enriched.append(review_row)

            counters["by_source"][str(row["source_id"])] += 1
            counters["by_family"][str(row["predicate_family"])] += 1
            counters["by_priority"][priority] += 1
            counters["by_previsual_label"][previsual_label] += 1
            counters["by_source_label"][(str(row["source_id"]), previsual_label)] += 1
            counters["by_family_label"][(str(row["predicate_family"]), previsual_label)] += 1
            counters["by_asset_state"][asset_state] += 1

    summary = {
        "schema_version": "h002_visual_annotation_audit_v0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_counts": input_counts,
        "total_rows": len(enriched),
        "final_label_options": FINAL_LABEL_OPTIONS,
        "counts": {
            "by_source": dict(sorted(counters["by_source"].items())),
            "by_family": dict(sorted(counters["by_family"].items())),
            "by_priority": dict(sorted(counters["by_priority"].items())),
            "by_previsual_label": dict(sorted(counters["by_previsual_label"].items())),
            "by_source_label": {
                f"{source}|{label}": count
                for (source, label), count in sorted(counters["by_source_label"].items())
            },
            "by_family_label": {
                f"{family}|{label}": count
                for (family, label), count in sorted(counters["by_family_label"].items())
            },
            "by_asset_state": dict(sorted(counters["by_asset_state"].items())),
        },
        "boundary": (
            "previsual_label is a metadata/asset-aided triage label, not a final "
            "human visual annotation. final_label remains null until manual image "
            "or point/mesh review is completed."
        ),
    }
    return enriched, summary


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def markdown_table(counter: dict[str, int], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    return lines


def write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    lines: list[str] = [
        "# H002 Visual Annotation Audit Preparation",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        summary["boundary"],
        "",
        "This report prepares the 288 sampled rows for manual visual/point review. It does not claim final labels.",
        "",
        "## Outputs",
        "",
        "- `review_queue.jsonl`: enriched queue with visual asset paths and previsual labels.",
        "- `previsual_summary.json`: counts and schema boundary.",
        "- `contact_sheets/`: generated for high-rank rows when rendering is enabled.",
        "",
        "## Counts",
        "",
        f"- Total rows: `{summary['total_rows']}`",
        "",
        "### Priority",
        "",
        *markdown_table(summary["counts"]["by_priority"], ("Priority", "Rows")),
        "",
        "### Visual Asset State",
        "",
        *markdown_table(summary["counts"]["by_asset_state"], ("Asset state", "Rows")),
        "",
        "### Previsual Labels",
        "",
        *markdown_table(summary["counts"]["by_previsual_label"], ("Previsual label", "Rows")),
        "",
        "### Source And Label",
        "",
        *markdown_table(summary["counts"]["by_source_label"], ("Source|label", "Rows")),
        "",
        "### Family And Label",
        "",
        *markdown_table(summary["counts"]["by_family_label"], ("Family|label", "Rows")),
        "",
        "## Next Step",
        "",
        "Fill `final_label` after manual image or point/mesh review. Prioritize `P0_top50` and `P1_top100_only` rows.",
        "",
    ]
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = H002_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows, summary = enrich_rows(args)
    write_jsonl(output_dir / "review_queue.jsonl", rows)
    with (output_dir / "previsual_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_report(output_dir, summary)

    print(
        f"rows={summary['total_rows']} "
        f"labels={summary['counts']['by_previsual_label']} "
        f"output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
