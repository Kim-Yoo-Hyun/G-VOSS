#!/usr/bin/env python3
"""Build the anonymous AAAI OpenReview release bundle from current locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


TITLE = "RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric Evidence"
TLDR = (
    "RelCompat3D uses geometric compatibility to re-rank fixed 3D scene graph "
    "relations, improving their Recall--Violation trade-off across three "
    "predictors."
)
ARCHIVE_ROOT = "relcompat3d_code_data"
SOURCE_DERIVED_ID_FILES = (
    "experiments/RelCompat3D_geom_reliability/"
    "factor_isolation_protocol/frozen_v1/manifest.json",
    "experiments/RelCompat3D_geom_reliability/"
    "no_family_indicator_v1/evaluation/counterfactual_sensitivity/summary.json",
    "experiments/RelCompat3D_geom_reliability/"
    "no_family_indicator_v1/evaluation/mlp_surface_audit/mechanism_rows.csv",
    "experiments/RelCompat3D_geom_reliability/"
    "no_family_indicator_v1/evaluation/surface_audit/mechanism_rows.csv",
    "experiments/RelCompat3D_geom_reliability/"
    "train_only_reestablishment_v1/splits/final_validation_scans.txt",
    "experiments/RelCompat3D_geom_reliability/"
    "train_only_reestablishment_v1/splits/internal_dev_scans.txt",
    "experiments/RelCompat3D_geom_reliability/"
    "train_only_reestablishment_v1/splits/method_development_scans.txt",
    "experiments/RelCompat3D_geom_reliability/"
    "train_only_reestablishment_v1/splits/train_scans.txt",
)
STABLE_ID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(repo: Path, staging: Path, relative: str) -> None:
    source = repo / relative
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = staging / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(
    repo: Path,
    staging: Path,
    relative: str,
    *,
    excluded_names: set[str] | None = None,
) -> None:
    source = repo / relative
    if not source.is_dir():
        raise FileNotFoundError(source)
    destination = staging / relative
    excluded_names = excluded_names or set()

    def ignore(_directory: str, names: list[str]) -> list[str]:
        return [
            name
            for name in names
            if name in excluded_names
            or name == "__pycache__"
            or name.endswith((".pyc", ".pyo"))
        ]

    shutil.copytree(source, destination, ignore=ignore)


def extract_abstract(repo: Path) -> str:
    text = (repo / "paper/aaai/sec/0_abstract.tex").read_text(encoding="utf-8")
    text = text.replace("\\begin{abstract}", "").replace("\\end{abstract}", "")
    return " ".join(text.replace("--", "–").replace("$", "").split())


def generated_readme() -> str:
    return """# RelCompat3D Code and Compact Data Supplement

This anonymous archive accompanies the AAAI-27 submission:

`RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric Evidence`

It contains the current executable method code, Docker configuration, frozen
  protocols and model hashes, compact evaluation summaries, and the exact LaTeX
sources and figures used for the main paper and technical supplement.

## Archive Map

- `src/relcompat3d/`: fitting, re-ranking, metrics, controls, intervals, audits,
  runtime measurement, and figure/table generation.
- `configs/relcompat3d/`: pinned Docker and Compose entry points.
- `scripts/run_no_family_indicator_v1.sh`: guarded active-protocol wrapper.
- `experiments/RelCompat3D_geom_reliability/`: active method pointer, frozen
  protocols, model locks, compact metrics, confidence intervals, controls, and
  point/mesh audits.
- `results/relcompat3d_geom_reliability/`: compact evidence index and report.
- `paper/`: current anonymous manuscript, supplement, checklist, bibliography,
  and active figure sources.
- `REPRODUCIBILITY.md`: reproduction tiers, external inputs, commands, and
  integrity checks.
- `MANIFEST.sha256`: SHA-256 digest of every other file in this archive.

## Reproduction Boundary

The archive supports source inspection, JSON/CSV validation, model-lock
verification, Python compilation, Docker configuration validation, and paper
rebuilding. Raw 3RScan/3DSSG data, stable source identifiers, source-derived
row bundles, source-predictor checkpoints, feature caches, and row-level
prediction/geometry payloads are not redistributed. Those external inputs are
required for full source inference and raw metric regeneration, as documented
in `REPRODUCIBILITY.md`.

No author identities, private repository links, or historical development
artifacts are included.
"""


def metadata(repo: Path, timestamp: str) -> str:
    abstract = extract_abstract(repo)
    return f"""# AAAI-27 Submission Metadata

Generated from the current anonymous source on {timestamp} KST.

## Paper Metadata

- Title: `{TITLE}`
- TL;DR: `{TLDR}`
- Recommended primary topic: `CV: 3D Computer Vision`
- Recommended secondary topics:
  - `CV: Object Detection, Segmentation & Scene Understanding`
  - `CV: Visual Reasoning & Symbolic Representations`
  - `ROB: Perception, Sensor Fusion & State Estimation`
  - `ML: Evaluation, Benchmarking, Datasets & Analysis`

## Abstract

{abstract}

## Claim Boundary

The paper reports scoped reliability evidence across three fixed predictors on
the shared 3DSSG validation scenes. It does not claim dataset-level
generalization, universal fusion optimality, or independent physical-validity
ground truth. The point- and mesh-based audit is an alternative geometric
measurement, not an independently annotated validity benchmark.

## Author Input Still Required

- Enter and verify the complete author list, order, profiles, affiliations, and
  conflicts in the submission system.
- Verify the live title, abstract, TL;DR, topics, reciprocal reviewer, and
  generative-AI disclosure and any required manuscript statement.
- Confirm that no concurrent submission violates the AAAI multiple-submission
  policy.
"""


def outer_readme(timestamp: str) -> str:
    return f"""# AAAI-27 OpenReview Upload Set

Generated from the current RelCompat3D manuscript and promoted method locks on
{timestamp} KST.

Upload each file to its matching field:

- `main.pdf`: anonymous main paper.
- `reproducibility_checklist.pdf`: standalone AAAI checklist.
- `technical_supplement.pdf`: anonymous technical supplement.
- `code_and_data_supplement.zip`: anonymous code and compact-data archive.

`UPLOAD_MANIFEST.sha256` records the exact outer files. The ZIP contains its own
`MANIFEST.sha256`.

Pre-flight status: the documents build without undefined citations,
references, or fatal LaTeX errors. The author must complete the required
generative-AI role documentation before upload.
"""


def write_manifest(root: Path, output: Path, excluded: set[Path] | None = None) -> None:
    excluded = {path.resolve() for path in (excluded or set())}
    lines = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.resolve() in excluded:
            continue
        lines.append(f"{sha256(path)}  {path.relative_to(root).as_posix()}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_zip(staging: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in staging.rglob("*") if p.is_file()):
            relative = Path(ARCHIVE_ROOT) / path.relative_to(staging)
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 7, 26, 0, 0, 0))
            mode = path.stat().st_mode & 0o777
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(args: argparse.Namespace) -> Path:
    repo = args.repo.resolve()
    build_root = args.build_root.resolve()
    timestamp = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    release = repo / "release" / f"relcompat3d_aaai27_openreview_{timestamp}"
    if release.exists():
        raise FileExistsError(release)
    release.mkdir(parents=True)

    pdf_inputs = {
        "main.pdf": build_root / "main/main.pdf",
        "technical_supplement.pdf": build_root / "supplement/supplement.pdf",
        "reproducibility_checklist.pdf": (
            build_root / "reproducibility/reproducibility_checklist_main.pdf"
        ),
    }
    for destination, source in pdf_inputs.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, release / destination)

    with tempfile.TemporaryDirectory(prefix="relcompat3d_code_data_") as temporary:
        staging = Path(temporary)

        copy_tree(repo, staging, "src/relcompat3d")
        copy_tree(repo, staging, "configs/relcompat3d")
        copy_file(repo, staging, "scripts/run_no_family_indicator_v1.sh")
        copy_file(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/commands.md",
        )
        copy_tree(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/factor_isolation_protocol",
            excluded_names={"models.json"},
        )
        copy_tree(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/train_only_reestablishment_v1",
            excluded_names={"models.json"},
        )
        copy_tree(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/no_family_indicator_v1",
            excluded_names={
                "README.md",
                "active_paper_lock.json",
                "models.json",
                "strict_models.json",
                "structured_models.json",
            },
        )
        copy_tree(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/score_robustness_v1",
        )
        copy_tree(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/routing_controls_v1",
        )
        copy_tree(
            repo,
            staging,
            "experiments/RelCompat3D_geom_reliability/construct_dependence_v1",
        )
        copy_tree(repo, staging, "results/relcompat3d_geom_reliability")

        # The upstream dataset terms do not explicitly authorize redistribution
        # of source-derived rows or stable scan/object identifiers. Keep the
        # anonymous archive on the conservative side of that boundary.
        for relative in SOURCE_DERIVED_ID_FILES:
            path = staging / relative
            if path.is_file():
                path.unlink()

        for root_name in ("experiments", "results"):
            root = staging / root_name
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in {
                    ".csv",
                    ".json",
                    ".jsonl",
                    ".md",
                    ".txt",
                    ".yaml",
                    ".yml",
                }:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if STABLE_ID_PATTERN.search(text):
                    raise RuntimeError(
                        f"stable source identifier remains in release: {path}"
                    )

        active_method_path = (
            repo / "experiments/RelCompat3D_geom_reliability/active_method.json"
        )
        active_method = json.loads(active_method_path.read_text(encoding="utf-8"))
        active_method["paper_release"] = {
            "selected_main": "main.pdf",
            "bundle": f"release/relcompat3d_aaai27_openreview_{timestamp}",
            "upload_manifest": (
                f"release/relcompat3d_aaai27_openreview_{timestamp}/"
                "UPLOAD_MANIFEST.sha256"
            ),
        }
        staged_active_method = (
            staging / "experiments/RelCompat3D_geom_reliability/active_method.json"
        )
        staged_active_method.parent.mkdir(parents=True, exist_ok=True)
        staged_active_method.write_text(
            json.dumps(active_method, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        paper_files = [
            "paper/references.bib",
            "paper/aaai/Dockerfile.tex",
            "paper/aaai/aaai2027.bst",
            "paper/aaai/aaai2027.sty",
            "paper/aaai/main.tex",
            "paper/aaai/supplement.tex",
            "paper/aaai/reproducibility_checklist.tex",
            "paper/aaai/reproducibility_checklist_main.tex",
            "paper/aaai/sec/0_abstract.tex",
            "paper/aaai/sec/1_introduction.tex",
            "paper/aaai/sec/2_related_work.tex",
            "paper/aaai/sec/3_method.tex",
            "paper/aaai/sec/4_experiments.tex",
            "paper/aaai/sec/5_discussion_limitations.tex",
            "paper/aaai/sec/6_conclusion.tex",
            "paper/aaai/sec/supplement.tex",
            "paper/aaai/supplement_figures/qualitative_geometry_panels.png",
            "paper/reference_AAAI/figure/Figure1.pdf",
            "paper/reference_AAAI/figure/Figure2.pdf",
            "paper/reference_AAAI/figure/Figure3.pdf",
        ]
        for relative in paper_files:
            copy_file(repo, staging, relative)

        shutil.copy2(repo / "docs/reproducibility.md", staging / "REPRODUCIBILITY.md")
        (staging / "README.md").write_text(generated_readme(), encoding="utf-8")
        manifest = staging / "MANIFEST.sha256"
        write_manifest(staging, manifest, excluded={manifest})
        write_zip(staging, release / "code_and_data_supplement.zip")

    (release / "README.md").write_text(outer_readme(timestamp), encoding="utf-8")
    (release / "submission_metadata.md").write_text(
        metadata(repo, timestamp), encoding="utf-8"
    )
    outer_manifest = release / "UPLOAD_MANIFEST.sha256"
    write_manifest(release, outer_manifest, excluded={outer_manifest})
    return release


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--build-root",
        type=Path,
        default=Path("/tmp/relcompat3d_release_build"),
    )
    parser.add_argument("--timestamp")
    return parser.parse_args()


if __name__ == "__main__":
    print(build(parse_args()))
