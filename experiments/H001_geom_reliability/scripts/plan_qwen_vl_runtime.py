#!/usr/bin/env python3
"""Plan Qwen-VL tiny-pilot crop rendering and model runtime gates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA_VERSION = "h001_qwen_vl_runtime_plan_v1"
PRIMARY_MODEL = {
    "role": "recommended_tiny_pilot_and_first_main",
    "model_id": "Qwen/Qwen3-VL-4B-Instruct",
    "revision": "ebb281ec70b05090aa6165b016eac8ec08e71b17",
    "local_name": "Qwen3-VL-4B-Instruct",
    "source": "https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct",
    "reason": "Most trend-aligned small dense Qwen3-VL target; use first for tiny pilot if crop rendering passes.",
}
FALLBACK_MODEL = {
    "role": "stable_small_fallback",
    "model_id": "Qwen/Qwen2.5-VL-3B-Instruct",
    "revision": "66285546d2b821cf421d4f5eb2576359d3770cd3",
    "local_name": "Qwen2.5-VL-3B-Instruct",
    "source": "https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct",
    "reason": "Stable smaller Qwen2.5-VL fallback if Qwen3-VL package/runtime friction blocks progress.",
}
PARSER_SMOKE_MODEL = {
    "role": "lowest_cost_parser_smoke",
    "model_id": "Qwen/Qwen3-VL-2B-Instruct",
    "revision": "89644892e4d85e24eaac8bacfd4f463576704203",
    "local_name": "Qwen3-VL-2B-Instruct",
    "source": "https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct",
    "reason": "Lowest-cost parser/runtime smoke candidate; not preferred for paper-quality evidence.",
}
QUALITY_FOLLOWUP_MODEL = {
    "role": "quality_followup_after_4b_pass",
    "model_id": "Qwen/Qwen3-VL-8B-Instruct",
    "revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
    "local_name": "Qwen3-VL-8B-Instruct",
    "source": "https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct",
    "reason": "Quality follow-up after the 4B path is stable and runtime budget permits.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--tiny-pilot-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/runtime_plan"),
    )
    parser.add_argument(
        "--model-cache-root",
        type=Path,
        default=Path("local_dataset/model_cache/huggingface/qwen_vl"),
    )
    parser.add_argument(
        "--views-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/output/datasets/OpenSG_3RScan/views"
        ),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def model_with_paths(repo_root: Path, cache_root: Path, item: dict[str, str]) -> dict[str, Any]:
    local_dir = cache_root / item["local_name"] / item["revision"]
    return {
        **item,
        "local_dir": relpath(repo_root, local_dir),
        "container_local_dir": f"/workspace/{relpath(repo_root, local_dir)}",
        "revision_lock_source": "git ls-remote refs/heads/main checked on 2026-05-08",
        "download_status": "not_started",
    }


def crop_records(repo_root: Path, tiny_rows: list[dict[str, Any]], views_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in tiny_rows:
        pair_paths = [item for item in row["crop_paths"] if item["role"] == "pair"]
        context_paths = [item for item in row["crop_paths"] if item["role"] == "context"]
        pair_path = resolve(repo_root, Path(pair_paths[0]["path"])) if pair_paths else None
        context_path = resolve(repo_root, Path(context_paths[0]["path"])) if context_paths else None
        object2image = views_dir / f"{row['scan_id']}_object2image.pkl"
        records.append(
            {
                "record_id": row["record_id"],
                "scan_id": row["scan_id"],
                "subgraph_id": row["subgraph_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "predicate_family": row["predicate_family"],
                "pair_crop_path": relpath(repo_root, pair_path),
                "pair_crop_exists": bool(pair_path and pair_path.exists()),
                "context_frame_path": relpath(repo_root, context_path),
                "context_frame_exists": bool(context_path and context_path.exists()),
                "object2image_metadata": relpath(repo_root, object2image),
                "object2image_metadata_exists": object2image.exists(),
                "render_status": "pending_pair_crop_render",
                "needed_before_runtime": [
                    "render pair crop image at reserved path",
                    "fill pair crop subject/object bboxes if available",
                    "rerun qwen_vl_tiny_pilot_validator after crop path update",
                ],
            }
        )
    return records


def render_commands(manifest: dict[str, Any]) -> str:
    primary = manifest["model_recommendation"]["models"][0]
    return f"""# Qwen-VL Runtime Plan Commands

These are future commands. They were not executed by this planning artifact.

Recommended first model:

```text
QWEN_VL_MODEL_ID={primary['model_id']}
QWEN_VL_MODEL_REVISION={primary['revision']}
QWEN_VL_LOCAL_DIR=/workspace/{primary['local_dir']}
```

Future resumable download template:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s qwen_vl_model_download \\
  "cd /home/yoohyun/research && huggingface-cli download {primary['model_id']} --revision {primary['revision']} --local-dir {primary['local_dir']} --local-dir-use-symlinks False > logs/qwen_vl_model_download_${{ts}}.log 2>&1"
```

Verification template after download:

```bash
find {primary['local_dir']} -maxdepth 2 -type f | wc -l
test -f {primary['local_dir']}/config.json
```
"""


def render_report(manifest: dict[str, Any]) -> str:
    primary = manifest["model_recommendation"]["models"][0]
    lines = [
        "# Qwen-VL Runtime Plan",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "This is a planning/preflight artifact only. It does not render crops, download a model, or run Qwen-VL inference.",
        "",
        "## Crop Preflight",
        "",
        f"- input rows: `{manifest['crop_preflight']['input_rows']}`",
        f"- pair crops existing: `{manifest['crop_preflight']['pair_crops_existing']}`",
        f"- pair crops missing: `{manifest['crop_preflight']['pair_crops_missing']}`",
        f"- context frames existing: `{manifest['crop_preflight']['context_frames_existing']}`",
        f"- object2image metadata existing: `{manifest['crop_preflight']['object2image_metadata_existing']}`",
        "",
        "## Recommended Model Lock",
        "",
        f"- model id: `{primary['model_id']}`",
        f"- revision: `{primary['revision']}`",
        f"- local dir: `{primary['local_dir']}`",
        "",
        "## Claim Boundary",
        "",
        "No Qwen-VL runtime evidence exists yet. This only fixes the next runtime gate and recommended model lock.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    tiny_pilot_dir = resolve(repo_root, args.tiny_pilot_dir)
    out_dir = resolve(repo_root, args.out)
    cache_root = resolve(repo_root, args.model_cache_root)
    views_dir = resolve(repo_root, args.views_dir)
    assert tiny_pilot_dir is not None
    assert out_dir is not None
    assert cache_root is not None
    assert views_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    tiny_manifest = load_json(tiny_pilot_dir / "manifest.json")
    tiny_rows = load_jsonl(tiny_pilot_dir / "input.jsonl")
    crops = crop_records(repo_root, tiny_rows, views_dir)
    family_counts = Counter(row["predicate_family"] for row in tiny_rows)
    pair_existing = sum(1 for row in crops if row["pair_crop_exists"])
    context_existing = sum(1 for row in crops if row["context_frame_exists"])
    metadata_existing = sum(1 for row in crops if row["object2image_metadata_exists"])

    errors: list[str] = []
    if tiny_manifest.get("status") != "tiny_pilot_scope_ready_no_model_runtime":
        errors.append(f"tiny_pilot_not_ready:{tiny_manifest.get('status')}")
    if len(tiny_rows) != 30:
        errors.append(f"tiny_pilot_input_rows:{len(tiny_rows)} expected:30")
    if context_existing != len(tiny_rows):
        errors.append(f"context_frames_existing:{context_existing} expected:{len(tiny_rows)}")
    if metadata_existing != len(tiny_rows):
        errors.append(f"object2image_metadata_existing:{metadata_existing} expected:{len(tiny_rows)}")

    models = [
        model_with_paths(repo_root, cache_root, PRIMARY_MODEL),
        model_with_paths(repo_root, cache_root, FALLBACK_MODEL),
        model_with_paths(repo_root, cache_root, PARSER_SMOKE_MODEL),
        model_with_paths(repo_root, cache_root, QUALITY_FOLLOWUP_MODEL),
    ]
    status = "runtime_plan_ready_no_model_download_no_inference" if not errors else "blocked_runtime_plan_errors"
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "runtime_policy": "no_crop_render_no_model_download_no_inference",
        "inputs": {
            "tiny_pilot_dir": relpath(repo_root, tiny_pilot_dir),
            "views_dir": relpath(repo_root, views_dir),
            "model_cache_root": relpath(repo_root, cache_root),
        },
        "outputs": {
            "crop_plan_jsonl": relpath(repo_root, out_dir / "crop_plan.jsonl"),
            "model_recommendation_json": relpath(repo_root, out_dir / "model_recommendation.json"),
            "commands_md": relpath(repo_root, out_dir / "commands.md"),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "crop_preflight": {
            "input_rows": len(tiny_rows),
            "family_counts": dict(sorted(family_counts.items())),
            "pair_crops_existing": pair_existing,
            "pair_crops_missing": len(tiny_rows) - pair_existing,
            "context_frames_existing": context_existing,
            "object2image_metadata_existing": metadata_existing,
            "crop_rendering_started": False,
        },
        "model_recommendation": {
            "checked_at": "2026-05-08",
            "method": "Hugging Face official pages plus git ls-remote refs/heads/main; no model files downloaded.",
            "decision": "Use Qwen3-VL-4B-Instruct first; fall back to Qwen2.5-VL-3B-Instruct if Qwen3 runtime support blocks progress.",
            "models": models,
        },
        "validation": {"errors": errors, "warnings": []},
        "next_action": "Render tiny-pilot pair crops before any Qwen model download/runtime smoke.",
    }
    write_jsonl(out_dir / "crop_plan.jsonl", crops)
    write_json(out_dir / "model_recommendation.json", manifest["model_recommendation"])
    (out_dir / "commands.md").write_text(render_commands(manifest), encoding="utf-8")
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
