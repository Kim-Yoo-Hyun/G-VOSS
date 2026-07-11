#!/usr/bin/env python3
"""Extract and hash one frozen official SceneGraphFusion checkpoint archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--member", required=True)
    parser.add_argument("--target-manifest", type=Path, required=True)
    parser.add_argument("--download-proof", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    archive = resolve(root, args.archive)
    target_manifest = resolve(root, args.target_manifest)
    download_proof = resolve(root, args.download_proof)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    target = json.loads(target_manifest.read_text(encoding="utf-8"))
    if target.get("status") != "target_frozen_pre_checkpoint_download_pre_inference":
        raise ValueError("target_not_frozen")
    if not download_proof.exists() or download_proof.read_text(encoding="utf-8").strip() != "0":
        raise ValueError("checkpoint_download_not_proven_complete")
    out.mkdir(parents=True, exist_ok=True)
    checkpoint = out / "model_best.pt"
    with zipfile.ZipFile(archive) as bundle:
        if args.member not in bundle.namelist():
            raise FileNotFoundError(f"checkpoint_member_missing:{args.member}")
        info = bundle.getinfo(args.member)
        with bundle.open(args.member) as source, checkpoint.open("wb") as target_handle:
            shutil.copyfileobj(source, target_handle)
    validations = {
        "checkpoint_nonempty": checkpoint.stat().st_size > 0,
        "uncompressed_size_matches_zip": checkpoint.stat().st_size == info.file_size,
        "download_completion_proof_postdates_target_freeze": download_proof.stat().st_mtime >= target_manifest.stat().st_mtime,
    }
    manifest = {
        "schema_version": "h001_scenegraphfusion_checkpoint_stage_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "3dssg_checkpoint_staged" if all(validations.values()) else "blocked_checkpoint_stage",
        "validations": validations,
        "archive": {"path": relpath(root, archive), "bytes": archive.stat().st_size, "sha256": digest(archive)},
        "member": args.member,
        "checkpoint": {"path": relpath(root, checkpoint), "bytes": checkpoint.stat().st_size, "sha256": digest(checkpoint)},
        "target_manifest": {"path": relpath(root, target_manifest), "sha256": digest(target_manifest)},
        "download_proof": {"path": relpath(root, download_proof), "sha256": digest(download_proof)},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "checkpoint": manifest["checkpoint"]}))
    return 0 if manifest["status"] == "3dssg_checkpoint_staged" else 2


if __name__ == "__main__":
    raise SystemExit(main())
