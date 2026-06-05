#!/usr/bin/env python3
"""Freeze the Docker runtime record for VL-SAT full-validation execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHECKPOINT_NAMES = (
    "clip_adapter_best.pth",
    "clip_model_best.pth",
    "config_best.pth",
    "lr_scheduler_best.pth",
    "mlp_3d_best.pth",
    "mmg_best.pth",
    "obj_encoder_best.pth",
    "obj_predictor_2d_best.pth",
    "obj_predictor_3d_best.pth",
    "optimizer_best.pth",
    "rel_encoder_2d_best.pth",
    "rel_encoder_3d_best.pth",
    "rel_predictor_2d_best.pth",
    "rel_predictor_3d_best.pth",
    "triplet_projector_2d_best.pth",
    "triplet_projector_3d_best.pth",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--scope-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/full_validation_transition/scope_contract"),
    )
    parser.add_argument(
        "--stage-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/vlsat/full_validation/stage"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/vlsat/full_validation/runtime_record"),
    )
    parser.add_argument(
        "--raw-preflight-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight"),
    )
    parser.add_argument(
        "--staged-root",
        type=Path,
        default=Path("local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT"),
    )
    parser.add_argument(
        "--vlsat-code-root",
        type=Path,
        default=Path("local_dataset/VLSAT_code/CVPR2023-VLSAT"),
    )
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("local_dataset/VLSAT_code/CVPR2023-VLSAT/output/ckp/Mmgnet/3dssg"),
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def checkpoint_records(repo_root: Path, checkpoint_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name in CHECKPOINT_NAMES:
        path = checkpoint_root / name
        records.append(
            {
                "name": name,
                "path": rel(repo_root, path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": sha256(path),
            }
        )
    return records


def build_commands(repo_root: Path) -> str:
    compose = "experiments/H001_geom_reliability/compose.yaml"
    lines = [
        "# VL-SAT Full-Validation Runtime Commands",
        "",
        "Status: `vlsat_full_validation_runtime_record_ready_no_metric_execution` if the manifest has no blockers.",
        "",
        "Run from the repository root. The raw dump is GPU/I/O-heavy and must run as a background job.",
        "",
        "## Stage Full Validation Runtime Root",
        "",
        "```bash",
        f"env UID=$(id -u) GID=$(id -g) docker compose -f {compose} run --rm --build vlsat_full_validation_stage",
        "```",
        "",
        "## Refresh Runtime Record",
        "",
        "```bash",
        f"env UID=$(id -u) GID=$(id -g) docker compose -f {compose} run --rm --build vlsat_full_validation_runtime_record",
        "```",
        "",
        "## Raw-Dump Preflight",
        "",
        "```bash",
        f"env UID=$(id -u) GID=$(id -g) docker compose -f {compose} run --rm vlsat_full_validation_raw_preflight",
        "```",
        "",
        "Expected preflight files:",
        "",
        "- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight/summary.json`",
        "- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight/report.md`",
        "",
        "## Raw Dump Background Job",
        "",
        "```bash",
        "mkdir -p logs",
        "ts=$(date +%Y%m%d_%H%M%S)",
        "tmux new-session -d -s h001_vlsat_full_validation_raw \"\\",
        f"cd {repo_root} && \\",
        f"env UID=\\$(id -u) GID=\\$(id -g) docker compose -f {compose} run --rm vlsat_full_validation_raw_dump \\",
        "> logs/vlsat_full_validation_raw_${ts}.log 2>&1; \\",
        "echo \\$? > logs/vlsat_full_validation_raw_${ts}.exit\"",
        "```",
        "",
        "Expected raw-dump files:",
        "",
        "- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/raw.jsonl`",
        "- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/summary.json`",
        "- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/report.md`",
        "- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/config.json`",
        "",
        "## Completion Verification",
        "",
        "```bash",
        "python - <<'PY'",
        "import json",
        "from pathlib import Path",
        "summary = Path('experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/summary.json')",
        "data = json.loads(summary.read_text())",
        "assert data['status'] == 'raw_dump_ready', data['status']",
        "assert data['counts']['selected_scans'] == 157, data['counts']",
        "assert data['counts']['dumped_subgraphs'] == 548, data['counts']",
        "print(json.dumps(data['counts'], sort_keys=True))",
        "PY",
        "```",
        "",
        "Promotion rule: this raw dump is still not a paper metric until adapter export, ground-truth JSONL, geometry join, metric evaluation, controls, GT verifier check, bootstrap CI, and table/report regeneration are all rerun under the same full-validation scope.",
        "",
    ]
    return "\n".join(lines)


def build_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    if manifest["raw_preflight"]["status"] == "ready_to_run" and manifest["raw_preflight"]["errors"] == 0:
        next_lines = [
            "1. Launch the raw dump as the documented timestamped tmux/background job when GPU contention is acceptable.",
            "2. After raw dump completion, run adapter export, ground-truth JSONL, geometry join, metrics, controls, GT verifier check, bootstrap CI, and table/report regeneration.",
            "3. Do not update paper tables until downstream full-validation metrics and bootstrap CI are regenerated.",
        ]
    else:
        next_lines = [
            "1. Run the Docker raw-dump preflight command in `commands.md`.",
            "2. If preflight passes, launch the raw dump as the documented tmux job.",
            "3. Do not update paper tables until downstream full-validation metrics and bootstrap CI are regenerated.",
        ]
    lines = [
        "# VL-SAT Full-Validation Runtime Record",
        "",
        f"Generated: `{manifest['generated_at']}`",
        f"Status: `{manifest['status']}`",
        "",
        "## Scope",
        "",
        f"- selected scans: `{counts['selected_scans']}`",
        f"- contexts: `{counts['contexts']}`",
        f"- expected VL-SAT prediction rows: `{counts['expected_vlsat_prediction_rows']}`",
        f"- H001-family GT rows: `{counts['h001_family_gt_rows']}`",
        "",
        "## Runtime",
        "",
        f"- runtime image: `{manifest['runtime']['image']}`",
        f"- staged root: `{manifest['paths']['staged_root']}`",
        f"- VL-SAT code root: `{manifest['paths']['vlsat_code_root']}`",
        f"- checkpoint root: `{manifest['paths']['checkpoint_root']}`",
        "",
        "## Readiness",
        "",
        f"- stage status: `{manifest['stage']['status']}`",
        f"- faithful ready scans: `{manifest['stage']['faithful_vlsat_ready_scans']}`",
        f"- raw preflight status: `{manifest['raw_preflight']['status']}`",
        f"- raw preflight errors: `{manifest['raw_preflight']['errors']}`",
        f"- raw preflight warnings: `{manifest['raw_preflight']['warnings']}`",
        f"- checkpoint files present: `{counts['checkpoint_files_present']}/{counts['checkpoint_files_expected']}`",
        "",
        "## Blockers",
        "",
    ]
    if manifest["blockers"]:
        lines.extend(f"- `{item}`" for item in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next",
            "",
            *next_lines,
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    scope_dir = (repo_root / args.scope_dir).resolve() if not args.scope_dir.is_absolute() else args.scope_dir
    stage_dir = (repo_root / args.stage_dir).resolve() if not args.stage_dir.is_absolute() else args.stage_dir
    out = (repo_root / args.out).resolve() if not args.out.is_absolute() else args.out
    raw_preflight_dir = (
        (repo_root / args.raw_preflight_dir).resolve()
        if not args.raw_preflight_dir.is_absolute()
        else args.raw_preflight_dir
    )
    staged_root = (repo_root / args.staged_root).resolve() if not args.staged_root.is_absolute() else args.staged_root
    vlsat_code_root = (
        (repo_root / args.vlsat_code_root).resolve()
        if not args.vlsat_code_root.is_absolute()
        else args.vlsat_code_root
    )
    checkpoint_root = (
        (repo_root / args.checkpoint_root).resolve()
        if not args.checkpoint_root.is_absolute()
        else args.checkpoint_root
    )

    scope_manifest = read_json(scope_dir / "manifest.json") or {}
    scope_contract = read_json(scope_dir / "scope_contract.json") or {}
    stage_manifest = read_json(stage_dir / "stage_manifest.json") or {}
    raw_preflight_summary = read_json(raw_preflight_dir / "summary.json") or {}
    selected_scans = read_lines(scope_dir / "scans.txt")
    contexts = read_lines(scope_dir / "contexts.jsonl")
    checkpoints = checkpoint_records(repo_root, checkpoint_root)

    scope_counts = (
        scope_contract.get("full_validation_scope")
        or scope_manifest.get("full_validation_scope")
        or scope_contract.get("counts")
        or scope_manifest.get("counts")
        or {}
    )
    stage_counts = stage_manifest.get("counts") or {}
    checkpoint_present = sum(1 for item in checkpoints if item["exists"])

    blockers: list[str] = []
    if not selected_scans:
        blockers.append("missing_or_empty_full_validation_scans_txt")
    if not contexts:
        blockers.append("missing_or_empty_full_validation_contexts_jsonl")
    if not stage_manifest:
        blockers.append("missing_vlsat_full_validation_stage_manifest")
    elif stage_manifest.get("status") != "ready":
        blockers.append(f"vlsat_stage_not_ready:{stage_manifest.get('status')}")
    if stage_counts.get("faithful_vlsat_ready_scans", 0) != len(selected_scans):
        blockers.append(
            "faithful_vlsat_ready_scan_count_mismatch:"
            f"{stage_counts.get('faithful_vlsat_ready_scans', 0)}/{len(selected_scans)}"
        )
    if not vlsat_code_root.exists():
        blockers.append(f"missing_vlsat_code_root:{rel(repo_root, vlsat_code_root)}")
    if checkpoint_present != len(CHECKPOINT_NAMES):
        blockers.append(f"missing_vlsat_checkpoint_files:{checkpoint_present}/{len(CHECKPOINT_NAMES)}")
    if raw_preflight_summary:
        preflight_validation = raw_preflight_summary.get("validation") or {}
        if preflight_validation.get("errors"):
            blockers.append(f"vlsat_raw_preflight_errors:{len(preflight_validation.get('errors', []))}")

    status = (
        "vlsat_full_validation_runtime_record_ready_no_metric_execution"
        if not blockers
        else "blocked_vlsat_full_validation_runtime_record"
    )
    manifest = {
        "schema_version": "h001_vlsat_full_validation_runtime_record_v1",
        "generated_at": now_iso(),
        "status": status,
        "runtime": {
            "image": "h001-open3dsg-repro:cu128",
            "reason": "existing CUDA 12.8 image already satisfies torch, CLIP, torch_scatter, torch_geometric, trimesh, open3d, and cv2 imports",
            "raw_dump_service": "vlsat_full_validation_raw_dump",
            "preflight_service": "vlsat_full_validation_raw_preflight",
            "stage_service": "vlsat_full_validation_stage",
        },
        "paths": {
            "scope_dir": rel(repo_root, scope_dir),
            "stage_dir": rel(repo_root, stage_dir),
            "staged_root": rel(repo_root, staged_root),
            "vlsat_code_root": rel(repo_root, vlsat_code_root),
            "checkpoint_root": rel(repo_root, checkpoint_root),
            "raw_preflight_dir": "experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight",
            "raw_dump_dir": "experiments/H001_geom_reliability/sources/vlsat/full_validation/raw",
        },
        "counts": {
            "selected_scans": len(selected_scans),
            "contexts": len(contexts),
            "candidate_directed_pairs": scope_counts.get("candidate_directed_pairs"),
            "expected_vlsat_prediction_rows": scope_counts.get(
                "expected_vlsat_prediction_rows_all_non_none_predicates"
            )
            or scope_counts.get("expected_vlsat_prediction_rows"),
            "gt_rows": scope_counts.get("gt_rows"),
            "h001_family_gt_rows": scope_counts.get("h001_family_gt_rows"),
            "checkpoint_files_expected": len(CHECKPOINT_NAMES),
            "checkpoint_files_present": checkpoint_present,
        },
        "stage": {
            "status": stage_manifest.get("status", "missing"),
            "stage_manifest": rel(repo_root, stage_dir / "stage_manifest.json"),
            "faithful_vlsat_ready_scans": stage_counts.get("faithful_vlsat_ready_scans", 0),
            "multi_view_ready_scans": stage_counts.get("multi_view_ready_scans", 0),
            "reference_aligned_mode": stage_manifest.get("reference_aligned_mode"),
        },
        "raw_preflight": {
            "status": raw_preflight_summary.get("status", "not_run"),
            "summary": rel(repo_root, raw_preflight_dir / "summary.json"),
            "report": rel(repo_root, raw_preflight_dir / "report.md"),
            "errors": len((raw_preflight_summary.get("validation") or {}).get("errors", [])),
            "warnings": len((raw_preflight_summary.get("validation") or {}).get("warnings", [])),
            "warning_items": (raw_preflight_summary.get("validation") or {}).get("warnings", []),
        },
        "checkpoints": checkpoints,
        "blockers": blockers,
        "promotion_rule": (
            "No full-validation VL-SAT output is paper metric evidence until raw dump, adapter export, "
            "ground-truth JSONL, geometry join, source metrics, controls, GT verifier check, bootstrap CI, "
            "and paper table/report regeneration all complete under the same full-validation scope."
        ),
    }

    write_json(out / "manifest.json", manifest)
    write_json(out / "runtime_contract.json", manifest)
    write_text(out / "commands.md", build_commands(repo_root))
    write_text(out / "report.md", build_report(manifest))
    print(json.dumps({"status": status, "blockers": blockers, "out": rel(repo_root, out)}, sort_keys=True))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
